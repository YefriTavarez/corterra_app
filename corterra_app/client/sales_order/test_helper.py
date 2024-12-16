# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import datetime
import unittest

from corterra_app.client.sales_order import helper


class TestHelper(unittest.TestCase):
	# 2024-12-23 -> 2024-12-23
	def test_get_next_working_day_2024_12_23(self):
		date = "2024-12-23"
		expected = datetime.date(2024, 12, 23)

		self.assertEqual(helper.get_next_working_day(date), expected)
	
	# 2024-12-24 -> 2024-12-24
	def test_get_next_working_day_2024_12_24(self):
		date = "2024-12-24"
		expected = datetime.date(2024, 12, 24)

		self.assertEqual(helper.get_next_working_day(date), expected)

	# 2024-12-25 -> 2024-12-26
	def test_get_next_working_day_2024_12_25(self):
		date = "2024-12-25"
		expected = datetime.date(2024, 12, 26)

		self.assertEqual(helper.get_next_working_day(date), expected)

	# 2024-12-28 -> 2024-12-30
	def test_get_next_working_day_2024_12_28(self):
		date = "2024-12-28"
		expected = datetime.date(2024, 12, 30)

		self.assertEqual(helper.get_next_working_day(date), expected)

	# 2024-12-29 -> 2024-12-30
	def test_get_next_working_day_2024_12_29(self):
		date = "2024-12-29"
		expected = datetime.date(2024, 12, 30)

		self.assertEqual(helper.get_next_working_day(date), expected)

	# 2024-12-30 -> 2024-12-30
	def test_get_next_working_day_2024_12_30(self):
		date = "2024-12-30"
		expected = datetime.date(2024, 12, 30)

		self.assertEqual(helper.get_next_working_day(date), expected)
