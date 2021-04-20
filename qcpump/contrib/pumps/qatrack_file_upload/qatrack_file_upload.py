from datetime import datetime

from pathlib import Path

from qcpump.pumps.base import STRING, BasePump, DIRECTORY, BOOLEAN, MULTCHOICE
from qcpump.pumps.common.qatrack import QATrackFetchAndPostTextFile, QATrackFetchAndPostBinaryFile


class BaseQATrackGenericUploader:

    TEST_LIST_CONFIG = {
        'name': "Test List",
        'multiple': False,
        'dependencies': ["QATrack+ API"],
        'validation': 'validate_test_list',
        'fields': [
            {
                'name': 'name',
                'type': STRING,
                'required': True,
                'help': "Enter the name of the Test List you want to upload data to.",
            },
            {
                'name': 'slug',
                'label': "Test Macro Name",
                'type': STRING,
                'required': True,
                'help': "Enter the macro name of the Upload test in this test list.",
                'default': 'upload',
            },
        ]
    }

    FILE_TYPE_CONFIGS = {
        'name': 'File Types',
        'fields': [
            {
                'name': 'recursive',
                'type': BOOLEAN,
                'required': True,
                'default': False,
                'help': "Should files from subdirectories be included?",
            },
            {
                'name': 'pattern',
                'type': STRING,
                'required': True,
                'default': "*",
                'help': (
                    "Enter a file globbing pattern (e.g. 'some-name-*.txt') to only "
                    "include certain files. Use '*' to include all files."
                ),
            },
            {
                'name': 'ignore pattern',
                'type': STRING,
                'required': True,
                'default': "",
                'help': (
                    "Enter a file globbing pattern (e.g. 'some-name-*.txt') to ignore "
                    "certain files. Leave blank to not exclude any files."
                ),
            },
        ],
    }

    DIRECTORY_CONFIG = {
        'name': 'Directories',
        'multiple': True,
        'validation': 'validate_source_dest',
        'dependencies': ["QATrack+ API"],
        'fields': [
            {
                'name': 'unit name',
                'label': "QATrack+ Unit Name",
                'type': MULTCHOICE,
                'required': True,
                'help': "Select the name of the unit in the QATrack+ database",
                'choices': 'get_qatrack_unit_choices',
            },
            {
                'name': 'source',
                'type': DIRECTORY,
                'required': True,
                'help': "Enter the root directory you want to read files from.",
            },
            {
                'name': 'destination',
                'type': DIRECTORY,
                'required': True,
                'help': (
                    "Enter the target directory that you want to move files to after they are uploaded. "
                    "(Leave blank if you don't want the files to be moved)"
                ),
            },
        ],
    }

    def validate_source_dest(self, values):
        """Ensure that source and destination directories are set."""
        valid = values['source'] and Path(values['source']).is_dir()
        msg = "OK" if valid else "You must set a valid source directory"
        return valid, msg

    def validate_test_list(self, values):
        """Ensure a test list name is given"""

        valid = bool(values['name'] and values['slug'])
        msgs = []
        if not values['name']:
            msgs.append("You must set a test list name")
        if not values['slug']:
            msgs.append("You must set a test macro name")

        return valid, "OK" if valid else '\n'.join(msgs)

    def fetch_records(self):

        searcher_config = self.get_config_values("File Types")[0]

        records = []
        self.move_to = {}
        for unit_dir in self.get_config_values("Directories"):
            path_searcher = searcher_config.copy()
            path_searcher.update(unit_dir)

            from_dir = path_searcher['source']
            to_dir = path_searcher['destination']

            paths = self.get_paths(path_searcher)
            for path in paths:
                move_to = Path(str(path).replace(from_dir, to_dir)) if to_dir else None
                records.append((unit_dir['unit name'], path, move_to))

        return records

    def post_process(self, record):
        unit, path, move_to = record

        try:
            move_to.parent.mkdir(parents=True, exist_ok=True)
            path.replace(move_to)
            msg = f"Moved {path} to {move_to}"
        except Exception as e:
            msg = f"Failed to move {path} to {move_to}: {e}"

        self.log_info(msg)

    def get_paths(self, mover):
        """Get a listing of all files in our source directory and filter them based on our config options"""
        globber = self.construct_globber(mover['pattern'], mover['recursive'])
        self.log_debug(f"Getting paths with globber: '{globber}' and mover: {mover}")
        all_paths = Path(mover['source']).glob(globber)
        return self.filter_paths(all_paths, mover['ignore pattern'])

    def construct_globber(self, pattern, recursive):
        """Consutruct a globber for reading from our source directory"""
        return f"**/{pattern}" if recursive else pattern

    def filter_paths(self, paths, ignore_pattern):
        """Filter out any paths that match our ignore pattern"""
        paths = (p for p in paths if not p.is_dir())
        if ignore_pattern in ["", None]:
            return list(paths)
        return [p for p in paths if not p.match(f"*/{ignore_pattern}")]

    def test_list_for_record(self, record):
        """Use the same test list name for all files"""
        return self.get_config_value("Test List", "name")

    def qatrack_unit_for_record(self, record):
        """Accept a record to process and return a QATrack+ Unit name. Must be overridden in subclasses"""
        unit, path, move_to = record
        return unit

    def id_for_record(self, record):
        unit, path, move_to = record
        modified = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        return f"QCPump/GenericTextFileUploader/{unit}/{modified}/{path.stem}"

    def slug_and_filename_for_record(self, record):
        unit, path, move_to = record
        slug = self.get_config_value("Test List", "slug")
        return slug, path.stem


class QATrackGenericTextFileUploader(BaseQATrackGenericUploader, QATrackFetchAndPostTextFile, BasePump):

    DISPLAY_NAME = "QATrack+ File Upload: Generic Text File"
    HELP_URL = "https://qcpump.qatrackplus.com/en/stable/pumps/qatrack_file_upload.html"

    CONFIG = [
        QATrackFetchAndPostTextFile.QATRACK_API_CONFIG,
        BaseQATrackGenericUploader.TEST_LIST_CONFIG,
        BaseQATrackGenericUploader.FILE_TYPE_CONFIGS,
        BaseQATrackGenericUploader.DIRECTORY_CONFIG,
    ]


class QATrackGenericBinaryFileUploader(BaseQATrackGenericUploader, QATrackFetchAndPostBinaryFile, BasePump):

    DISPLAY_NAME = "QATrack+ File Upload: Generic Binary File"
    HELP_URL = "https://qcpump.qatrackplus.com/en/stable/pumps/qatrack_file_upload.html"

    CONFIG = [
        QATrackFetchAndPostTextFile.QATRACK_API_CONFIG,
        BaseQATrackGenericUploader.TEST_LIST_CONFIG,
        BaseQATrackGenericUploader.FILE_TYPE_CONFIGS,
        BaseQATrackGenericUploader.DIRECTORY_CONFIG,
    ]
