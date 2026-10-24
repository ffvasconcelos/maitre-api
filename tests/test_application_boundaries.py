import subprocess
import sys


def test_application_imports_without_loading_infrastructure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            "import maitre_api.application.services; "
            "import maitre_api.application.ports; "
            "import maitre_api.application.ports.unit_of_work; "
            "assert not any(name.startswith("
            "('maitre_api.infrastructure', 'sqlalchemy', 'fastapi')) "
            "for name in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
