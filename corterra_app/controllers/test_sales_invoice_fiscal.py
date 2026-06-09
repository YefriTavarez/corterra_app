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
			"docstatus": 0,
			"ncf_status": "Never Sent",
			"flags": types.SimpleNamespace(),
		}
		defaults.update(kwargs)
		return types.SimpleNamespace(**defaults)

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
		):
			self.assertTrue(fiscal.assign_encf_to_invoice(doc))

		self.assertEqual(doc.ncf, "E310000000001")
		self.assertEqual(doc.sequence_due_date, "2026-12-31")
		self.assertTrue(doc.flags.corterra_encf_auto_assigned)

	def test_assign_encf_to_invoice_skips_when_ncf_exists(self):
		doc = self._doc(ncf="E310000000099")
		with patch.object(fiscal, "should_use_nubef_fiscal", return_value=True), patch.object(
			fiscal, "get_sequence_info"
		) as get_sequence_info:
			self.assertFalse(fiscal.assign_encf_to_invoice(doc))
			get_sequence_info.assert_not_called()

	def test_assign_encf_to_invoice_noops_for_non_alanube_company(self):
		doc = self._doc()
		with patch.object(fiscal, "should_use_nubef_fiscal", return_value=False), patch.object(
			fiscal, "get_sequence_info"
		) as get_sequence_info:
			self.assertFalse(fiscal.assign_encf_to_invoice(doc))
			get_sequence_info.assert_not_called()

	def test_send_to_alanube_if_needed_sends_auto_assigned_invoice(self):
		doc = self._doc(
			ncf="E310000000001",
			flags=types.SimpleNamespace(corterra_encf_auto_assigned=True),
		)
		with patch.object(fiscal, "_send_to_alanube") as send_to_alanube:
			self.assertTrue(fiscal.send_to_alanube_if_needed(doc))

		send_to_alanube.assert_called_once_with("FACT-0001")
		self.assertTrue(doc.flags.skip_auto_post_to_alanube)
		self.assertTrue(doc.flags.corterra_encf_sent_to_alanube)

	def test_send_to_alanube_if_needed_skips_without_auto_assign_flag(self):
		doc = self._doc(ncf="E310000000001")
		with patch.object(fiscal, "_send_to_alanube") as send_to_alanube:
			self.assertFalse(fiscal.send_to_alanube_if_needed(doc))
			send_to_alanube.assert_not_called()

	def test_send_to_alanube_if_needed_skips_already_sent(self):
		doc = self._doc(
			ncf="E310000000001",
			flags=types.SimpleNamespace(
				corterra_encf_auto_assigned=True,
				corterra_encf_sent_to_alanube=True,
			),
		)
		with patch.object(fiscal, "_send_to_alanube") as send_to_alanube:
			self.assertFalse(fiscal.send_to_alanube_if_needed(doc))
			send_to_alanube.assert_not_called()

	def test_ensure_encf_before_submit_pre_sends_when_deferred(self):
		doc = self._doc()
		with patch.object(fiscal, "assign_encf_to_invoice", return_value=True) as assign_encf, patch.object(
			fiscal, "should_defer_erpnext_submit_until_alanube_receipt", return_value=True
		), patch.object(fiscal, "send_to_alanube_if_needed", return_value=True) as send_if_needed:
			fiscal.ensure_encf_before_submit(doc)

		assign_encf.assert_called_once_with(doc)
		send_if_needed.assert_called_once_with(doc)

	def test_ensure_encf_before_submit_skips_pre_send_when_not_deferred(self):
		doc = self._doc()
		with patch.object(fiscal, "assign_encf_to_invoice", return_value=True), patch.object(
			fiscal, "should_defer_erpnext_submit_until_alanube_receipt", return_value=False
		), patch.object(fiscal, "send_to_alanube_if_needed") as send_if_needed:
			fiscal.ensure_encf_before_submit(doc)

		send_if_needed.assert_not_called()

	def test_send_encf_to_alanube_delegates_to_send_if_needed(self):
		doc = self._doc()
		with patch.object(fiscal, "send_to_alanube_if_needed", return_value=True) as send_if_needed:
			fiscal.send_encf_to_alanube(doc)
			send_if_needed.assert_called_once_with(doc)
