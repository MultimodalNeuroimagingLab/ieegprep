# define directory as package


#
# ensure minimum version of python
#
import sys
if sys.version_info < (3, 8, 0):
    sys.exit("Python 3.8 or later is required.")


#
# Pre-check some dependencies (and in particular their versions) at runtime
# Note 1: added since, despite the (minimum) requirements during install, packages can be downgraded or removed later
# Note 2: deliberately not in a separate module, since this is the entry point of the package and dependencies already be used after
#
from configparser import ConfigParser
from importlib.metadata import version, PackageNotFoundError
from re import sub as re_sub, split as re_split
def normalize_version(v):
    return [int(x) for x in re_sub(r'(\.0+)*$','', v).split(".")]

cf = ConfigParser()
cf.read('setup.cfg')
require_lines = [x for x in cf.get('options', 'install_requires').strip().splitlines()]

for req_line in require_lines:
    for req_line_part in req_line.split(','):
        req_args = re_split('>=|==', req_line_part.strip())
        if len(req_args) == 2:
            req_args[0] = req_args[0].strip()
            req_args[1] = req_args[1].strip()
            try:
                current_version = version(req_args[0])
                if normalize_version(current_version) < normalize_version(req_args[1]):
                    sys.exit('Dependency \'' + req_args[0] + '\' is installed but outdated: the current version is \'' + current_version + '\', while version ' + req_args[1] + ' or higher is required.\n'
                             'Execute \'pip install --upgrade ' + req_args[0] + '\' in the command-line prompt/terminal to update the package\n')
            except PackageNotFoundError as err:
                sys.exit('Dependency \'' + req_args[0] + '\' is required but not installed.\n'
                         'Execute \'pip install ' + req_args[0] + '\' in the command-line prompt/terminal to install the package\n')


#
# flatten access
#
from ieegprep.version import __version__
from ieegprep.bids.data_epoch import load_data_epochs, load_data_epochs_averages
from ieegprep.bids.data_structure import list_bids_datasets
from ieegprep.bids.rereferencing import RerefStruct
from ieegprep.bids.sidecars import load_event_info, load_stim_event_info, load_channel_info, load_ieeg_sidecar
from ieegprep.fileio.IeegDataReader import VALID_FORMAT_EXTENSIONS, IeegDataReader
