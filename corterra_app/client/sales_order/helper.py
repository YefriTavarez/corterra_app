# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING, Union

import frappe
from frappe.utils import getdate, add_days

if TYPE_CHECKING:
	import datetime


__all__ = (
	"get_next_working_day",
)


def get_next_working_day(date: Union["datetime.date", "str"]) -> "datetime.date":
	"""
	Get the next working day of the given date using the ERPNext Holiday List doctype.
	"""

	if isinstance(date, str):
		date = getdate(date)

	# allow to test the current date if it's a holiday
	# date = add_days(date, 1)

	while frappe.db.exists("Holiday", {
		"holiday_date": date.strftime("%Y-%m-%d")
	}):
		date = add_days(date, 1)

	return date
