from pathlib import Path

from qcpump.pumps.base import BOOLEAN, DIRECTORY, STRING, BasePump


class SimpleFileMover(BasePump):

    CONFIG = [
        {
            'name': 'SimpleFileMover',
            'multiple': True,
            'validation': 'validate_source_dest',
            'fields': [
                {
                    'name': 'source',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Enter the source directory you want move files out of.",
                },
                {
                    'name': 'destination',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Enter the target directory that you want move files to.",
                },
            ],
        },
    ]

    def validate_source_dest(self, values):
        """Ensure that both source and destination directories are set."""

        valid = bool(values['source'] and values['destination'])

        msg = []
        if not values['source']:
            msg.append("You must set a source directory")
        if not values['destination']:
            msg.append("You must set a destination directory")

        return valid, ','.join(msg) or 'OK'

    def pump(self):

        moved = []
        self.log_debug("Starting to pump")
        terminate = False
        for mover in self.get_config_values("SimpleFileMover"):

            paths = list(Path(mover['source']).glob("*"))
            to_dir = Path(mover['destination'])

            self.log_info(f"Found {len(paths)} files to move.")
            for f in paths:

                # your pumps should always periodically check whether they
                # should terminate
                terminate = self.should_terminate()
                if terminate:
                    break

                try:
                    dest = to_dir / f.name
                    f.replace(dest)
                    msg = f"Moved {f} to {to_dir / f.name}"
                except Exception:
                    msg = f"Failed to move {f} to {to_dir / f.name}"

                self.log_info(msg)
                moved.append(msg)

            if terminate:
                self.log_debug("Terminating early")
                break

        self.log_debug("Finished Pumping")

        return '\n'.join(moved)


class FileMover(BasePump):

    CONFIG = [
        {
            'name': 'FileMover',
            'multiple': True,
            'validation': 'validate_source_dest',
            'fields': [
                {
                    'name': 'source',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Enter the source directory you want move files out of.",
                },
                {
                    'name': 'destination',
                    'type': DIRECTORY,
                    'required': True,
                    'help': "Enter the target directory that you want move files to.",
                },
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
        },
    ]

    def validate_source_dest(self, values):
        """Ensure that both source and destination directories are set."""

        valid = bool(values['source'] and values['destination'])

        msg = []
        if not values['source']:
            msg.append("You must set a source directory")
        if not values['destination']:
            msg.append("You must set a destination directory")

        return valid, '\n'.join(msg) or 'OK'

    def pump(self):

        moved = []
        self.log_debug("Starting to pump")
        terminate = False
        for mover in self.get_config_values("FileMover"):

            paths = self.get_paths(mover)

            to_dir = Path(mover['destination'])

            self.log_info(f"Found {len(paths)} files to move.")
            for f in paths:

                # your pumps should always periodically check whether they should terminate
                terminate = self.should_terminate()
                if terminate:
                    break

                try:
                    dest = to_dir / f.name
                    f.replace(dest)
                    msg = f"Moved {f} to {to_dir / f.name}"
                except Exception:
                    msg = f"Failed to move {f} to {to_dir / f.name}"

                self.log_info(msg)
                moved.append(msg)

            if terminate:
                self.log_debug("Terminating early")
                break

        self.log_debug("Finished Pumping")

        return '\n'.join(moved)

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
        if ignore_pattern in ["", None]:
            return list(paths)
        return [p for p in paths if not p.match(f"*/{ignore_pattern}")]
