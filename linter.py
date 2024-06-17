import sys
from pylint.lint import Run

def run_pylint():
    Run(sys.argv[1:])