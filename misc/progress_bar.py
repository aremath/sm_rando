# Credit to Greenstick (StackOverflow)

def print_progress_bar(current_iteration, total_iterations, prefix="", suffix="", decimals=1, length=50, fill="█"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * current_iteration / total_iterations)
    filled_length = (length * current_iteration) // total_iterations
    bar = fill * filled_length + "-" * (length - filled_length)
    print("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix), end="\r")
    # Print newline on complete
    if current_iteration == total_iterations:
        print()

