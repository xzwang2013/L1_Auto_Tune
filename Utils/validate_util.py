import os
import sys
import getopt


def doRun(argv):
    try:
        opts, args = getopt.getopt(argv, "s:c:k:j:")
    except getopt.GetoptError:
        print "error parsing arguments"
        return

    stc_app_dir = None
    comm_dir = None
    key = None
    json_str = None
    for opt, arg in opts:
        if opt == "-k":
            key = arg
        elif opt == "-j":
            json_str = arg
        elif opt == "-s":
            stc_app_dir = arg
        elif opt == "-c":
            comm_dir = arg

    if not stc_app_dir or not os.path.isdir(stc_app_dir):
        print "invalid stc app directory (-s switch)"
        return
    if not comm_dir or not os.path.isdir(comm_dir):
        print "invalid stc comm user directory (-c switch)"
        return

    if not key:
        print "invalid schema key (-k switch)"
        return
    if not json_str:
        print "invalid JSON (-j switch)"
        return

    stak_path = os.path.join(comm_dir, "STAKCommands")
    py_lib_path = os.path.join(stc_app_dir, "Python", "lib", "site-packages")
    if not os.path.isdir(stak_path):
        print "STAKCommands path: {0} is not a valid directory".format(stak_path)
        return
    if not os.path.isdir(py_lib_path):
        print "Python lib path: {0} is not a valid directory".format(py_lib_path)
        return

    if stak_path not in sys.path:
        sys.path.append(stak_path)
    if py_lib_path not in sys.path:
        sys.path.append(py_lib_path)

    import spirent.methodology.utils.schema_utils as schema_utils
    import spirent.methodology.utils.json_utils as json_utils
    # Get the schema
    err_str, schema_str = schema_utils.get_schema(key)
    if err_str:
        print "Error getting schema {0}: {1}".format(key, err_str)
        return False

    # Validate against the schema
    err_str = json_utils.validate_json(json_str, schema_str, err_str_limit=0)
    if err_str:
        print err_str
        return

    # err_str = schema_utils.get_schema_and_validate_json(key, json_str)
    # if err_str:
    #     print err_str


if __name__ == '__main__':
    doRun(sys.argv[1:])
    sys.exit()
