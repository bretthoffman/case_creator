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
        selected = template_rules.build_template_path(override_template_key, case_data)

    return _apply_itero_outsource_template_reroute(selected, case_data)


def _apply_itero_outsource_template_reroute(template_path, case_data):
    """
    Outsource iTero cases use the same template families as non-iTero outsource for
    study/anterior (itero_* -> reg_*). Posterior ai_adzir/ai_envision reroute to
    itero_outsource_* (digital impression, ModelBuilder off). Designer iTero keeps
    the baseline selection.
    """
    from domain.decisions.delivery_mode_selector import MODE_OUTSOURCE, resolve_delivery_mode
    from domain.rules import template_rules

    cd = case_data or {}
    if resolve_delivery_mode(cd) != MODE_OUTSOURCE:
        return template_path
    if not template_rules.is_itero_scanner(cd.get("scanner", "")):
        return template_path

    folder = os.path.basename(os.path.dirname(template_path))
    remapped = template_rules.remap_itero_folder_for_outsource(folder)
    if remapped == folder:
        return template_path

    _LOGGER.info(
        "case_creator_itero_outsource_template_reroute scanner=%r baseline_template=%r "
        "rerouted_template=%r",
        cd.get("scanner"),
        folder,
        remapped,
    )
    return template_rules.build_template_path(remapped, case_data)
