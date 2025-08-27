import json

import matplotlib.pyplot as plt


def plot_and_save_time_series_from_json(
    json_filename, output_image_filename="time_series_plot.png"
):
    with open(json_filename, "r") as f:
        time_series_data = json.load(f)

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    axs = axs.flatten()

    for idx, (series_name, series_info) in enumerate(time_series_data.items()):
        data = series_info["data"]
        axs[idx].plot(data, marker="o", linestyle="-", markersize=4)
        axs[idx].set_title(series_name)
        axs[idx].set_xlabel("Time")
        axs[idx].set_ylabel("Value")
        axs[idx].grid(True)

    plt.tight_layout()

    plt.savefig(output_image_filename)
    plt.close()  # Close the figure to free up memory
    print(f"Plot saved to '{output_image_filename}'")


def main():
    plot_and_save_time_series_from_json(
        json_filename="test_time_series.json",
        output_image_filename="test_time_series_plot.png",
    )


if __name__ == "__main__":
    main()
