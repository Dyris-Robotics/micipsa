import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from ament_index_python.packages import get_package_share_directory


# Test Fixture: Xacro File Location
# ---------------------------------
# Description:
#   Locates the robot URDF Xacro file from the installed
#   micipsa_description package share directory.
#
# Success Criteria:
# - The package share directory is found.
# - The micipsa_urdf.xacro file exists.
@pytest.fixture(scope="session")
def robot_xacro_file() -> Path:
    pkg_share = Path(get_package_share_directory("micipsa_description"))
    xacro_file = pkg_share / "urdf" / "micipsa_urdf.xacro"

    if not xacro_file.exists():
        pytest.fail(f"xacro file not found: {xacro_file}")

    return xacro_file


# Test Fixture: Xacro Executable
# ------------------------------
# Description:
#   Locates the `xacro` executable in the system PATH so tests
#   can invoke it to generate URDF from Xacro.
#
# Success Criteria:
# - xacro executable is found.
# - If not found, the test is skipped because URDF generation
#   cannot be performed.
@pytest.fixture(scope="session")
def xacro_exe() -> str:
    exe = shutil.which("xacro")

    if exe is None:
        pytest.skip(
            "xacro executable not found (is ros-xacro installed and environment sourced?)"
        )

    return exe


# Test Fixture: check_urdf Executable (Optional)
# ----------------------------------------------
# Description:
#   Attempts to locate the `check_urdf` tool used to validate
#   URDF structure and kinematic consistency.
#
# Success Criteria:
# - If check_urdf exists, it will be used to validate the URDF.
# - If not installed, URDF validation is skipped.
@pytest.fixture(scope="session")
def check_urdf_exe() -> str | None:
    return shutil.which("check_urdf")


# Helper Function: Run Xacro
# --------------------------
# Description:
#   Executes the Xacro command-line tool to convert the robot
#   Xacro file into a URDF XML string.
#
# Success Criteria:
# - Xacro execution completes successfully.
# - Output URDF XML is non-empty.
def run_xacro(xacro_exe: str, xacro_file: Path, *, deploy_mode: str) -> str:
    proc = subprocess.run(
        [xacro_exe, str(xacro_file), f"deploy_mode:={deploy_mode}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )

    assert (
        proc.returncode == 0
    ), f"xacro failed (deploy_mode={deploy_mode}):\n{proc.stderr}"

    urdf_xml = proc.stdout.strip()
    assert urdf_xml, "xacro produced empty output"

    return urdf_xml


# Helper Function: URDF XML Validation
# ------------------------------------
# Description:
#   Verifies that the generated URDF XML can be parsed and that
#   the root element is a valid <robot> tag.
#
# Success Criteria:
# - XML parsing succeeds.
# - Root tag is <robot>.
# - Robot tag contains a name attribute.
def assert_urdf_is_parseable(urdf_xml: str) -> None:
    root = ET.fromstring(urdf_xml)

    assert root.tag == "robot", f"Expected root <robot>, got <{root.tag}>"
    assert root.attrib.get("name"), "URDF <robot> must have a name attribute"


# Helper Function: Optional URDF Structural Validation
# ----------------------------------------------------
# Description:
#   Uses the `check_urdf` utility (if available) to perform deeper
#   validation of the URDF model including kinematic consistency.
#
# Success Criteria:
# - If check_urdf is available, the URDF passes validation.
# - If not available, the validation step is skipped.
def maybe_check_urdf(check_urdf_exe: str | None, urdf_xml: str) -> None:
    if check_urdf_exe is None:
        pytest.skip("check_urdf not installed; skipping check_urdf validation")

    proc = subprocess.run(
        [check_urdf_exe, "-"],
        input=urdf_xml,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 0, f"check_urdf failed:\n{proc.stderr}"


# Test Case: Xacro Generates Valid URDF
# -------------------------------------
# Description:
#   Verifies that the micipsa_urdf.xacro file can be successfully
#   converted into a valid URDF for both deployment configurations.
#
# Test Variants:
# - deploy_mode = false (simulation configuration)
# - deploy_mode = true  (hardware deployment configuration)
#
# Success Criteria:
# - Xacro conversion completes without errors.
# - Generated URDF XML is valid and parseable.
# - URDF root element is <robot> with a valid name.
# - If available, check_urdf confirms structural correctness.
@pytest.mark.parametrize("deploy_mode", ["false", "true"])
def test_urdf_generation_validity(
    xacro_exe: str,
    robot_xacro_file: Path,
    check_urdf_exe: str | None,
    deploy_mode: str,
) -> None:
    urdf_xml = run_xacro(xacro_exe, robot_xacro_file, deploy_mode=deploy_mode)

    assert_urdf_is_parseable(urdf_xml)

    maybe_check_urdf(check_urdf_exe, urdf_xml)
