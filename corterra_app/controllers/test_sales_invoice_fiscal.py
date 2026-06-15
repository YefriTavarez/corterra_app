# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

import types
import unittest
from unittest.mock import MagicMock, patch

from corterra_app.controllers import sales_invoice_fiscal as fiscal


class TestSalesInvoiceFiscal(unittest.TestCase):
	def _doc(self, **kwargs):
		defaults = {
			"doctype": "Sales Invoice",
			"name": "FACT-0001",
			"company": "ACME",
			"customer": "CUST-001",
			"docstatus": 1,
			"ncf_status": "Never Sent",
			"reload": MagicMock(),
			"db_set": MagicMock(),
			"save": MagicMock(),
			"get": lambda self, key, default=None: getattr(self, key, default),
		}
		defaults.update(kwargs)
		doc = types.SimpleNamespace(**defaults)
		doc.get = lambda key, default=None: getattr(doc, key, default)
		return doc

	def test_should_use_nubef_fiscal_when_alanube_company_manages_ncfs(self):
		doc = self._doc()
		with patch.object(fiscal, "is_alanube_company", return_value=True), patch.object(
			fiscal,
			"get_alanube_company_details",
			return_value={"enabled": 1, "manage_ncfs_from_alanubes": 1},
		):
			self.assertTrue(fiscal.should_use_nubef_fiscal(doc))

	def test_should_use_nubef_fiscal_false_for_non_alanube_company(self):
		doc = self._doc()
		with patch.object(fiscal, "is_alanube_company", return_value=False):
			self.assertFalse(fiscal.should_use_nubef_fiscal(doc))

	def test_assign_encf_to_invoice_consumes_suggested_sequence(self):
		doc = self._doc()
		with patch.object(fiscal, "should_use_nubef_fiscal", return_value=True), patch.object(
			fiscal, "_resolve_sequence_name", return_value="SEQ-E31"
		), patch.object(
			fiscal, "get_sequence_info", return_value=("SEQ-E31", "E310000000001", "2026-12-31")
		), patch.object(
			fiscal, "_populate_dgii_reference_information"
		), patch.object(fiscal, "_persist_submitted_encf") as persist:
			self.assertTrue(fiscal.assign_encf_to_invoice(doc))

		self.assertEqual(doc.ncf, "E310000000001")
		self.assertEqual(doc.sequence_due_date, "2026-12-31")
		persist.assert_called_once_with(doc, "E310000000001", "2026-12-31")

	def test_assign_encf_to_invoice_skips_when_ncf_exists(self):
		doc = self._doc(ncf="E310000000099")
		with patch.object(fiscal, "should_use_nubef_fiscal", return_value=True), patch.object(
			fiscal, "get_sequence_info"
		) as get_sequence_info:
			self.assertFalse(fiscal.assign_encf_to_invoice(doc))
			get_sequence_info.assert_not_called()

	def test_send_pending_invoice_to_alanube_sends_submitted_invoice(self):
		doc = self._doc(ncf="E310000000001")
		with patch.object(fiscal, "_send_to_alanube") as send_to_alanube:
			self.assertTrue(fiscal.send_pending_invoice_to_alanube(doc))

		send_to_alanube.assert_called_once_with("FACT-0001")

	def test_send_pending_invoice_to_alanube_skips_without_ncf(self):
		doc = self._doc(ncf="")
		with patch.object(fiscal, "_send_to_alanube") as send_to_alanube:
			self.assertFalse(fiscal.send_pending_invoice_to_alanube(doc))
			send_to_alanube.assert_not_called()

	def test_get_pending_sales_invoice_names_merges_missing_ncf_and_pending_send(self):
		with patch.object(fiscal, "get_alanube_fiscal_companies", return_value=["ACME"]), patch.object(
			fiscal, "frappe"
		) as mock_frappe:
			mock_frappe.get_all.side_effect = [["FACT-0001"], ["FACT-0002", "FACT-0001"]]
			self.assertEqual(
				fiscal.get_pending_sales_invoice_names(),
				["FACT-0001", "FACT-0002"],
			)

	def test_process_sales_invoice_fiscal_assigns_then_sends(self):
		doc = self._doc(ncf="")

		def assign_side_effect(invoice):
			invoice.ncf = "E310000000001"
			return True

		with patch.object(fiscal, "frappe") as mock_frappe, patch.object(
			fiscal, "should_use_nubef_fiscal", return_value=True
		), patch.object(
			fiscal, "assign_encf_to_invoice", side_effect=assign_side_effect
		) as assign_encf, patch.object(
			fiscal, "send_pending_invoice_to_alanube", return_value=True
		) as send_pending:
			mock_frappe.get_doc.return_value = doc
			self.assertTrue(fiscal.process_sales_invoice_fiscal("FACT-0001"))

		assign_encf.assert_called_once_with(doc)
		doc.reload.assert_called_once_with()
		send_pending.assert_called_once_with(doc)

	def test_process_pending_sales_invoice_fiscal_commits_success_and_logs_failures(self):
		with patch.object(
			fiscal, "get_pending_sales_invoice_names", return_value=["FACT-0001", "FACT-0002"]
		), patch.object(
			fiscal, "process_sales_invoice_fiscal", side_effect=[True, Exception("boom")]
		), patch.object(
			fiscal, "frappe"
		) as mock_frappe:
			mock_frappe.get_traceback.return_value = "traceback"
			fiscal.process_pending_sales_invoice_fiscal()

		self.assertEqual(mock_frappe.db.commit.call_count, 1)
		mock_frappe.db.rollback.assert_called_once()
		mock_frappe.log_error.assert_called_once()
