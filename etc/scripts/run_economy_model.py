import matplotlib.pyplot as plt
from pandas import DataFrame, read_parquet

from process.vis.utils import convert_png_to_gif

syspop_base_path = (
    "/DSC/digital_twin/abm/synthetic_population/v3.01/Wellington/syspop_base.parquet"
)
syspop_diary_path = (
    "/DSC/digital_twin/abm/synthetic_population/v3.01/Wellington/syspop_diaries.parquet"
)

syspop_location_path = "/DSC/digital_twin/abm/synthetic_population/v3.01/Wellington/syspop_location.parquet"

abm_output_path = (
    "/DSC/digital_twin/abm/DT_demo/v2.1/baseline/output/output_model_1_ens_0.parquet"
)

abm_output = read_parquet(abm_output_path)
abm_output["id"] = abm_output["id"].astype(int)

abm_diary = read_parquet(syspop_diary_path)

abm_location = read_parquet(syspop_location_path)

restaurant_names = abm_location[
    (abm_location["area"] == 241800)
    & (abm_location["type"].isin(["restaurant", "cafe"]))
].drop_duplicates()["name"]

abm_diary = abm_diary.dropna()

visitor_ids = abm_diary[abm_diary["location"].isin(restaurant_names)]["id"].unique()


all_steps = abm_output.step.unique()

total_person = len(visitor_ids) / len(all_steps)

remove_percentage = {}

for i, proc_step in enumerate(all_steps):

    infected_person = abm_output[
        (abm_output["step"] == proc_step)
        & (abm_output["infected_flag"] == 1)
        & (abm_output["id"].isin(visitor_ids))
    ]
    recovered_person = abm_output[
        (abm_output["step"] == proc_step)
        & (abm_output["recovered_flag"] == 1)
        & (abm_output["id"].isin(visitor_ids))
    ]

    person_to_remove = len(infected_person) - len(recovered_person)

    remove_percentage[proc_step] = round((person_to_remove / total_person) * 100.0, 2)

    print(f"{proc_step}: ")
    print(f" - infected_person: {len(infected_person)}")
    print(f" - recovered_person: {len(recovered_person)}")
    print(f" - remove_percentage: {remove_percentage[proc_step]}")


df = DataFrame(list(remove_percentage.items()), columns=["Date", "Value"])

# Set the date as the index
df.set_index("Date", inplace=True)

df["Value"] = df["Value"].apply(lambda x: x if x <= 100.0 else 100.0)
df["Value"] = df["Value"].apply(lambda x: x if x >= 0.0 else 0.0)
all_files = []
for i in range(len(df)):
    # Plot the dataframe as a timeseries
    plt.figure(figsize=(10, 5))
    plt.plot(100.0 - df[:i]["Value"])

    plt.xticks(df.index[::10], rotation=45)  # Set labels for every 2nd date
    plt.xlim(df.index.min(), df.index.max())
    plt.ylim(0, 102)
    plt.title(
        "Relative Income Growth Rate, baseline, 100% \n Sector: restaurant + cafe; Region: 241800"
    )
    plt.xlabel("Date")
    plt.ylabel("Relative Income Change Rate")
    plt.tight_layout()
    plt.savefig(f"test_{i}.png")
    all_files.append(f"test_{i}.png")

convert_png_to_gif(all_files, "income_change_rate.gif", 150)
