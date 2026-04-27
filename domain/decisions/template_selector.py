import logging
import os

_LOGGER = logging.getLogger(__name__)


def select_template_path(case_data):
    """
    Thin compatibility shell for template decisioning.
    Delegates to the current authoritative template precedence logic.
    """
    # Local import prevents module-cycle issues during incremental migration.
    from config import doctor_outcomes_live_enabled
    from template_utils import select_template
    from domain.rules import template_rules
    from infrastructure.config.doctor_override_runtime import (
        resolve_doctor_template_override_with_source,
    )

    selected = select_template(case_data)
    doctor_name = (case_data or {}).get("doctor", "")
    override_template_key, override_source = resolve_doctor_template_override_with_source(
        doctor_name, case_data
    )

    if (
        doctor_outcomes_live_enabled()
        and override_source == "outcomes"
        and override_template_key
    ):
        baseline_folder = os.path.basename(os.path.dirname(selected))
        if override_template_key != baseline_folder:
            _LOGGER.info(
                "case_creator_doctor_outcomes_override doctor=%r baseline_template=%r "
                "override_template=%r",
                doctor_name,
                baseline_folder,
                override_template_key,
            )

    if override_template_key:
        return template_rules.build_template_path(override_template_key)

    return selected
