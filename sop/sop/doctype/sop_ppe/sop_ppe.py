# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

from frappe.utils.nestedset import NestedSet


class SOPPPE(NestedSet):
	nsm_parent_field = "parent_sop_ppe"
