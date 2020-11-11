import os
import sys
import traceback
from StcIntPythonPL import CStcSystem


def create_venv(venv_name):
    '''
    create_venv uses the same procedure within the STC BLL to copy a virtual
    environment to the appropriate place for use. In the end, a script is
    called to do the installation
    '''
    if not venv_name:
        return False
    stc_sys = CStcSystem.Instance()
    common_data_path = stc_sys.GetApplicationCommonDataPath()
    user_stak_virtualenv_path = stc_sys.GetStakVirtualEnvPath()
    install_path = stc_sys.GetApplicationInstallPath()
    session_data_path = stc_sys.GetApplicationSessionDataPath()
    prev_path = sys.path
    venv_script_dir = \
        os.path.normpath(os.path.join(common_data_path, 'STAKvirtualenvs'))
    # Temporarily add the copy script path into the system path
    sys.path.append(venv_script_dir)
    import stakvirtualenv as sve

    # Fill parameters with defaults
    packages = []
    venv_parent_dir = os.path.normpath(user_stak_virtualenv_path)
    arg_upgrade = True
    arg_remove = True
    pkg_dir = os.path.normpath(os.path.join(common_data_path,
                                            'STAKvirtualenvs',
                                            '__packages__'))
    req_file = os.path.normpath(os.path.join(common_data_path,
                                             'STAKvirtualenvs',
                                             '__requirements__',
                                             venv_name +
                                             '_requirements.txt'))
    log_file = os.path.normpath(os.path.join(session_data_path, venv_name +
                                             '_install.log'))
    # Save stdout
    old_stdout = sys.stdout
    with open(log_file, 'w') as fd:
        # Redirect output
        sys.stdout = fd

        # Use block file lock to ensure that only one process can
        # create the virtualenv.
        print "Now locking {}".format(os.path.join(venv_parent_dir,
                                                   venv_name))
        import flock
        with flock.FLock(str(os.path.join(venv_parent_dir, venv_name)) +
                         '.lock'):
            try:
                venv_path = sve.setup_venv(install_path, packages, venv_name,
                                           venv_parent_dir, arg_upgrade,
                                           arg_remove, pkg_dir, req_file)
                sve.generate_code(venv_path, install_path)
            except ValueError as e:
                # It's ok if there's a path mismatch
                if 'path is on' not in str(e) or 'start on' not in str(e):
                    print "Failed to create virtual environment: {}" \
                        .format(traceback.format_exc())
                    return False
            except:
                print "Failed to create virtual environment: {}" \
                    .format(traceback.format_exc())
                # We failed somehow, just return False which will fail the
                # comparison
                return False
            finally:
                # Restore stdout
                sys.stdout = old_stdout
                del sve
                del flock
                sys.path = prev_path
    return True


def enable_venv(venv_name):
    '''
    Enables the virtual environment with the given name. Returns True on
    passing. If the virtual environment has not been installed, calls
    create_venv to install the environment
    '''
    if not venv_name:
        return False
    stc_sys = CStcSystem.Instance()
    user_stak_virtualenv_path = stc_sys.GetStakVirtualEnvPath()
    bin_dir = 'Scripts' if os.name == 'nt' else 'bin'
    script = os.path.normpath(os.path.join(user_stak_virtualenv_path,
                                           venv_name, bin_dir,
                                           'activate_this.py'))
    if not os.path.exists(script):
        if not create_venv(venv_name):
            return False
    # Assumption is made regarding the activation script: Subsequent adds
    # should not affect operations, but we need to check if the script fails
    # in some way
    try:
        execfile(script, dict(__file__=script))
    except:
        # If an exception is thrown as this script is run, we need to flag it
        return False
    return True
