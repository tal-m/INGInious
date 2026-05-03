from inginious.frontend.environment_types.generic_docker_oci_runtime import GenericDockerOCIRuntime
from inginious.common.constants import EXTRA_CAPABILITIES

class KataEnvType(GenericDockerOCIRuntime):
    @property
    def id(self):
        return "kata-ssh" if self._ssh_allowed else "kata"

    @property
    def name(self):
        return _("Container running as root (Kata) + SSH") if self._ssh_allowed else _("Container running as root (Kata)")

    def check_task_environment_parameters(self, data):
        out = super().check_task_environment_parameters(data)
        # Add capabilities to grading container?
        for cap in EXTRA_CAPABILITIES:
            out[cap] = data.get(cap, False)

        return out