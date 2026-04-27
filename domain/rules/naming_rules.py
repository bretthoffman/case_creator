from dataclasses import dataclass

from domain.rules import routing_rules

ARGEN_SUFFIX = "os"
ITERO_SUFFIX = "i"


@dataclass(frozen=True)
class CaseNamingDecision:
    suffix: str
    final_case_id: str


def build_case_naming(case_id: str, template_path_or_name: str, scanner_name: str) -> CaseNamingDecision:
    """
    Preserve current naming behavior:
    - append 'os' when template is Argen
    - append 'i' when scanner contains iTero
    - append as combined single suffix with underscore, only when non-empty
    """
    suffix = ""
    template_name = routing_rules.template_filename(template_path_or_name)
    scanner = (scanner_name or "").lower()

    if routing_rules.is_argen_template(template_name):
        suffix += ARGEN_SUFFIX
    if "itero" in scanner:
        suffix += ITERO_SUFFIX

    if suffix:
        return CaseNamingDecision(suffix=suffix, final_case_id=f"{case_id}_{suffix}")
    return CaseNamingDecision(suffix="", final_case_id=case_id)
