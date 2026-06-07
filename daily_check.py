from release_checker import (
    check_movies
)

from tv_checker import (
    check_tv_shows
)


if __name__ == "__main__":

    print(
        "Running Movie Checks..."
    )

    check_movies()

    print(
        "\nRunning TV Checks..."
    )

    check_tv_shows()

    print(
        "\nAll checks completed."
    )