"""Main command-line entry-point and any code tightly coupled to it.
"""
import sys
import os
import argparse
import textwrap
from vex import config
from vex.run import make_env, run


def _barf(message):
    """Standard way of reporting an error and bailing.
    """
    sys.stdout.write("Error: " + message + '\n')
    sys.exit(1)


def get_command(options, vexrc, environ):
    command = options.rest
    if not command:
        command = vexrc.get_shell(environ)
    return command


def make_arg_parser():
    """Return a standard ArgumentParser object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        usage="vex [OPTIONS] VIRTUALENV_NAME COMMAND_TO_RUN ...",
    )

    parser.add_argument(
        "--path",
        metavar="DIR",
        help="absolute path to virtualenv to use",
        action="store"
    )
    parser.add_argument(
        '--cwd',
        metavar="DIR",
        action="store",
        default='.',
        help="path to run command in (default: '.' aka $PWD)",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=os.path.expanduser('~/.vexrc'),
        action="store",
        help="path to config file to read (default: '~/.vexrc')"
    )
    parser.add_argument(
        "rest",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS)

    return parser


def main_logic(environ, argv):
    """Logic for main(), without the direct system interactions.
    """
    # Get options, complain if any unknown stuff crept in
    arg_parser = make_arg_parser()
    options, unknown = arg_parser.parse_known_args(argv)
    if unknown:
        arg_parser.print_help()
        return _barf("unknown args: {0!r}".format(unknown))

    vexrc = config.Vexrc.from_file(options.config, environ)
    ve_base = vexrc.get_ve_base(environ)
    if not options.path and not ve_base:
        return _barf(
            "could not figure out a virtualenvs directory. "
            "make sure $HOME is set, or $WORKON_HOME,"
            " or set virtualenvs=something in your .vexrc")
    if not os.path.exists(ve_base):
        return _barf("virtualenvs directory {0!r} not found.".format(ve_base))

    # Find a virtualenv path
    ve_path = options.path
    ve_name = None
    if ve_path:
        ve_name = os.path.basename(os.path.normpath(ve_path))
    else:
        ve_name = options.rest.pop(0) if options.rest else None
        if not ve_name:
            _barf("could not find a virtualenv name in the command line.")
            arg_parser.print_help()
            return 1
        ve_path = os.path.join(ve_base, ve_name)
    assert ve_path
    assert isinstance(ve_path, str)
    ve_path = os.path.abspath(ve_path)
    if not ve_name:
        ve_name = os.path.basename(os.path.normpath(ve_path))
    if not os.path.exists(ve_path):
        return _barf("virtualenv not found at {0!r}.".format(ve_path))
    options.path = ve_path
    options.virtualenv = ve_name

    command = get_command(options, vexrc, environ)
    if not command:
        return _barf("no command")
    env = make_env(environ, vexrc['env'], options)
    returncode = run(command, env=env, cwd=options.cwd)
    if returncode is None:
        return _barf("command not found: {0!r}".format(command[0]))
    return returncode


def main():
    """The main command-line entry point, with system interactions.
    """
    argv = sys.argv[1:]
    returncode = main_logic(os.environ, argv)
    sys.exit(returncode)