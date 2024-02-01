#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_shuf.py

Interactive tester for CS 35L Homework 2 (shuf.py).

Make sure you have a file test_input in the same directory. It should
contain newline-separated entries to be used as input for the file
options to shuf.py.

Make sure you have a file test_cases in the same directory.
Usage instructions are included in the provided file.

Usage on the SEASnet server::

    python3 test_shuf.py [OPTIONS]
"""

__author__ = "Vincent Lin"

import os
import subprocess
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from enum import Enum, auto

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.traceback import install

# pylint: disable=anomalous-backslash-in-string

# Set up rich output
console = Console()
install(console=console)

# Parser for a script about parsing, how meta
parser = ArgumentParser(description="Interactive tester for shuf.py.")
parser.add_argument(
    "-l", "--list",
    action="store_true",
    help="list the parsed test cases from test_cases and exit"
)
parser.add_argument(
    "-c", "--custom-only",
    action="store_true",
    help="only list or run your custom test cases"
)
inclusion = parser.add_mutually_exclusive_group()
inclusion.add_argument(
    "-i", "--include",
    nargs="*",
    metavar="CASE_NUMS",
    help="include only these test cases (as numbered in --list)"
)
inclusion.add_argument(
    "-e", "--exclude",
    nargs="*",
    metavar="CASE_NUMS",
    help="exclude these test cases (as numbered in --list)"
)


class Status(Enum):
    """Test case status as determined by tester."""
    PENDING = auto()
    ACCEPTED = auto()
    MARKED = auto()
    AUTO_MARKED = auto()
    SKIPPED = auto()
    GO_BACK = auto()


@dataclass
class TestCase:
    """Represents a single test case loaded from test_cases."""

    num: int
    """The unique case number for easier reference."""
    line_num: int
    """The line number this case corresponds to in test_cases."""
    command: str
    """
    The string containing the options to pass to both the tester's
    shuf.py and the GNU shuf.
    """
    comment: str | None
    """
    The comment associated with the test case, for convenience. The
    leading '# ' is stripped when initialized. Set to None if there is
    no comment within reasonable proximity of the case line.
    """
    custom: bool
    """
    Whether this test case is one defined after the 'Your Custom Cases'
    barrier and thus not one that I provided with test_shuf.tgz.
    """
    status: Status
    """
    How the tester responded to this test case. To be set at runtime.
    Useful for generating the final summary message.
    """


def center_print(*args, **kwargs) -> None:
    """Shortcut for justifying a console.print() to the center."""
    console.print(*args, justify="center", **kwargs)


def clear_screen(message: str | None = None, color: str | None = None) -> None:
    """Clear the terminal screen to reduce clutter.

    Arguments:
        message (str | None): Optional message to display at the top of
        the screen after clearing it. If None or empty, no message is
        displayed.
        color (str | None): Color to style the optional message with.
        If None or empty, the default color is used.
    """
    os.system("cls" if os.name == "nt" else "clear")
    if message:
        color = color or None
        panel = Panel(message,
                      style=Style(color=color, bold=True),
                      width=os.get_terminal_size()[0])
        center_print(panel)


def get_original_command() -> str:
    """Get italicized string representing invocation of this script."""
    return "[italic]$ python3 " + escape(" ".join(sys.argv)) + "[/]"


def load_test_cases(include: list[str] | None,
                    exclude: list[str] | None,
                    custom_only: bool
                    ) -> tuple[list[TestCase], int, int]:
    """Parse the test_cases file and initialize the TestCases.

    Arguments:
        include (list[str] | None): List of numbers of cases the list
        should entirely include, if provided.
        exclude (list[str] | None): List of case numbers to exclude, if
        provided. Precondition: include and exclude will not be
        simultaneously given, by mutually exclusive options.
        custom_only (bool): Whether only custom test cases should be
        returned.

    Returns:
        tuple[list[TestCase], int, int]: A 3-tuple containing the list
        of TestCase objects, the number of pre-made test cases, and the
        number of tester-defined custom test cases among the list.
    """
    test_cases = []
    # Keep track of the context of the following command(s)
    current_comment: str | None = None
    past_custom_barrier = False
    case_num = 1
    num_custom = 0

    if exclude is None:
        exclude_nums = {}
    else:
        exclude_nums = {int(num) for num in exclude}

    if include is None:
        include_nums = {}
    else:
        include_nums = {int(num) for num in include}

    with open("test_cases", "rt", encoding="utf-8") as fp:
        for line_num, line in enumerate(fp, start=1):
            # Reasonable people would separate the cases into chunks
            if line.isspace():
                current_comment = None
                continue

            if line == "#      Your Custom Cases      #\n":
                past_custom_barrier = True
                continue

            if custom_only and not past_custom_barrier:
                continue

            if line.startswith("#"):
                current_comment = line.rstrip()
                continue

            # At this point, we're sure that line is a command

            # Inclusion/exclusion logic
            if case_num in exclude_nums:
                case_num += 1
                continue
            if include is not None and case_num not in include_nums:
                case_num += 1
                continue

            command = line.rstrip()
            # Special token
            if command == "`":
                command = ""

            # Process the comment associated with this test case
            comment = None
            if current_comment is not None:
                comment = current_comment.lstrip("# ")
            test_case = TestCase(num=case_num,
                                 line_num=line_num,
                                 command=command,
                                 comment=comment,
                                 custom=past_custom_barrier,
                                 status=Status.PENDING)
            test_cases.append(test_case)

            case_num += 1
            if past_custom_barrier:
                num_custom += 1

    return (test_cases, len(test_cases) - num_custom, num_custom)


def print_test_cases(test_cases: list[TestCase]) -> None:
    """List the test cases out in a readable format for the tester."""
    table = Table(title=f"Test Cases\n{get_original_command()}")
    table.add_column("Num",
                     justify="right",
                     style=Style(color="cyan", bold=True))
    table.add_column("Line", justify="right")
    table.add_column("Options")
    table.add_column("Context", style="bright_black")
    table.add_column("Custom")
    for test_case in test_cases:
        context = test_case.comment or ""
        table.add_row(str(test_case.num),
                      str(test_case.line_num),
                      test_case.command,
                      context,
                      str(test_case.custom))
    center_print(table)


def run_test_case(test_case: TestCase, num_left: int) -> bool:
    """Run a single test case.

    Arguments:
        test_case (TestCase): Test case to run.
        num_left (int): Number of test cases left for display purposes.

    Returns:
        bool: Return whether the program should continue iterating
        through test cases after this test case. In other words, return
        False if the user chose to quit and True otherwise.
    """
    # In case this test cases is revisited by retrying or going back
    test_case.status = Status.PENDING

    # Information header
    case_info = (
        f"[cyan]TEST CASE {test_case.num} ({num_left} left)[/]\n"
        f"[yellow]Context:[/] [default]{test_case.comment or ''}[/]\n"
        f"[yellow]Options:[/] [default]{test_case.command}[/]"
    )
    header = Panel(case_info,
                   style="cyan",
                   width=os.get_terminal_size()[0])
    center_print(header)
    console.print()

    # Run the commands
    gnu_stdout, gnu_stderr, gnu_retcode = run_process(True, test_case.command)
    py_stdout, py_stderr, py_retcode = run_process(False, test_case.command)

    # Auto-mark this test case for obvious differences
    wrong_retcode = wrong_stdout_presence = wrong_stderr_presence = False

    if gnu_retcode != py_retcode:
        test_case.status = Status.AUTO_MARKED
        wrong_retcode = True
    if (gnu_stdout == "" and py_stdout != "") \
            or (py_stdout == "" and gnu_stdout != ""):
        test_case.status = Status.AUTO_MARKED
        wrong_stdout_presence = True
    if (gnu_stderr == "" and py_stderr != "") \
            or (py_stderr == "" and gnu_stderr != ""):
        test_case.status = Status.AUTO_MARKED
        wrong_stderr_presence = True

    # Post-processing to make ambiguous output more clear in the table
    gnu_stdout = gnu_stdout or "[bright_black]<NO STDOUT>[/]"
    py_stdout = py_stdout or "[bright_black]<NO STDOUT>[/]"
    gnu_stderr = gnu_stderr or "[bright_black]<NO STDERR>[/]"
    py_stderr = py_stderr or "[bright_black]<NO STDERR>[/]"

    # Prepare and output comparison table
    table = Table(title="Output Comparison (GNU <--> YOURS)",
                  show_lines=True,
                  header_style="bold cyan")

    table.add_column(f"$ shuf {test_case.command}")
    table.add_column(f"$ python3 shuf.py {test_case.command}")

    table.add_row(gnu_stdout,
                  py_stdout,
                  style="red" if wrong_stdout_presence else None)
    table.add_row(gnu_stderr,
                  py_stderr,
                  style="red" if wrong_stderr_presence else None)
    table.add_row(f"[yellow]Exit code:[/] {gnu_retcode}",
                  f"[yellow]Exit code:[/] {py_retcode}",
                  style="red" if wrong_retcode else None)

    console.print()
    center_print(table)

    # Automatically marked by my algorithm
    if test_case.status is Status.AUTO_MARKED:
        panel = Panel(
            "Your presence/absence of output and/or return code does not match "
            "that of GNU shuf. The offending comparison is styled in red. This "
            "test case is AUTO-MARKED for you."
        )
        center_print(panel, style="red")
        center_print(
            "\n[green]\[r]etry | \[b]ack | \[q]uit | "
            "RET or anything else to CONTINUE:[/]\n"
        )
    else:
        center_print(
            "\n[green]\[s]kip | \[m]ark | \[r]etry | \[b]ack | \[q]uit | "
            "RET or anything else to ACCEPT:[/]\n"
        )
    try:
        response = console.input("[bold]> [/]").lower()
        match response:
            case "q" | "quit":
                raise KeyboardInterrupt
            case "s" | "skip" if test_case.status is not Status.AUTO_MARKED:
                test_case.status = Status.SKIPPED
            case "m" | "marked" if test_case.status is not Status.AUTO_MARKED:
                test_case.status = Status.MARKED
            case "r" | "retry":
                test_case.status = Status.PENDING
            case "b" | "back":
                test_case.status = Status.GO_BACK
            case _ if test_case.status is not Status.AUTO_MARKED:
                test_case.status = Status.ACCEPTED
    except (KeyboardInterrupt, EOFError):
        return False

    return True


def run_process(gnu: bool, args: str) -> tuple[str, str, int | None]:
    """Run a shuf implementation in a subprocess.

    Arguments:
        gnu (bool): True if we're running the GNU shuf. False if we're
        running the tester's shuf.py script.
        args (str): The command line options to use.

    Returns:
        tuple[str, str, int | None]: A 3-tuple containing the stdout,
        stderr, and return code of the child process. stdout == stderr
        == "<INTERRUPTED>" and return code is None if interrupted.
    """
    head = "shuf" if gnu else "python3 shuf.py"
    # If the program expects input, user will see this message
    # Otherwise, it'll be covered by clear_screen()
    console.print(
        f"[yellow]STDIN for {'GNU shuf' if gnu else 'shuf.py'} "
        "(use RET C-d to finish or C-c to cancel):[/]"
    )
    with subprocess.Popen(f"{head} {args}",
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE
                          ) as child:
        try:
            stdout, stderr = child.communicate()
        # Bro I can't get this working, child.stdout.flush() doesn't work either
        except KeyboardInterrupt:
            return ("<INTERRUPTED>", "<INTERRUPTED>", None)
        return (stdout.decode("utf-8"),
                stderr.decode("utf-8"),
                child.returncode)


def print_summary(test_cases: list[TestCase]) -> None:
    """Print a summary table of the test cases."""
    unreached = Table(title="Summary: [bold bright_black]UNREACHED[/] Cases")
    skipped = Table(title="Summary: [bold yellow]SKIPPED[/] Cases")
    marked = Table(title="Summary: [bold red]MARKED[/] Cases")

    for table, color in zip((unreached, skipped, marked),
                            ("bright_black", "yellow", "red")):
        table.add_column("Num",
                         justify="right",
                         style=Style(color="cyan", bold=True))
        table.add_column("Line", justify="right")
        table.add_column("Options", style=color)
        table.add_column("Context", style="bright_black")

    for test_case in test_cases:
        table = None
        match test_case.status:
            case Status.PENDING:
                table = unreached
            case Status.SKIPPED:
                table = skipped
            case Status.MARKED | Status.AUTO_MARKED:
                table = marked
        if table is not None:
            num = test_case.num
            line_num = test_case.line_num
            options = test_case.command
            context = test_case.comment or ""
            table.add_row(str(num), str(line_num), options, context)

    # Output the tables if they have any content
    for table, name, color in zip((unreached, skipped, marked),
                                  ("unreached", "skipped", "marked"),
                                  ("bright_black", "yellow", "red")):
        if table.row_count > 0:
            console.print()
            center_print(table)
        else:
            center_print(
                f"\nSummary: No [bold {color}]{name.upper()}[/] cases. "
                "Well done!",
                style=Style(italic=True))

    console.print()


def main() -> None:
    """Main driver function."""
    # Parse command line arguments
    namespace = parser.parse_args()

    # Load test cases
    test_cases, num_provided, num_custom = load_test_cases(
        namespace.include,
        namespace.exclude,
        namespace.custom_only
    )

    # Only list them if -l/--list used
    if namespace.list:
        clear_screen()
        print_test_cases(test_cases)
        center_print(
            f"\n[yellow]Loaded {len(test_cases)} ({num_provided} provided, "
            f"{num_custom} custom) test cases![/]\n"
        )
        return

    # Run the test cases
    message = color = ""
    index = 0
    while index < len(test_cases):
        clear_screen(message, color)

        test_case = test_cases[index]
        num_left = len(test_cases) - (index + 1)
        still_running = run_test_case(test_case=test_case,
                                      num_left=num_left)
        if not still_running:
            message = f"Script ended early. You ran:\n{get_original_command()}"
            color = "red"
            break

        # Prepare the flash header for the NEXT iteration
        match test_case.status:
            case Status.ACCEPTED:
                message = "You ACCEPTED the previous comparison"
                color = "green"
            case Status.SKIPPED:
                message = "You SKIPPED the previous comparison"
                color = "yellow"
            case Status.MARKED:
                message = "You MARKED the previous comparison"
                color = "red"
            case Status.AUTO_MARKED:
                message = "The previous comparison was AUTO-MARKED"
                color = "red"
            case Status.PENDING:
                message = "You are RETRYING this current test case"
                color = "cyan"
                continue
            case Status.GO_BACK:
                message = "You're REVISITING the previous test case"
                color = "blue"
                # You're not getting me with this edge case lol
                index = max(0, index - 1)
                continue
            # I don't know how this would happen but just in case
            case _:
                message = color = ""

        message += ("\n[italic]You can use \[b]ack to revisit "
                    "the previous test case[/]")
        index += 1

    else:
        message = ("You ran all test cases as loaded by:\n"
                   f"{get_original_command()}")
        color = "green"

    clear_screen(message, color)
    print_summary(test_cases)


if __name__ == "__main__":
    main()
