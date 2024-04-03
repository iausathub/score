import csv

with open("test_observations.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "satellite_name",
            "norad_cat_id",
            "observation_time_utc",
            "observation_time_uncertainty_sec",
            "apparent_magnitude",
            "apparent_magnitude_uncertainty",
            "observer_latitude_deg",
            "observer_longitude_deg",
            "observer_altitude_m",
            "instrument",
            "observing_mode",
            "observing_filter",
            "observer_email",
            "observer_orcid",
            "satellite_right_ascension_deg",
            "satellite_right_ascension_uncertainty_deg",
            "satellite_declination_deg",
            "satellite_declination_uncertainty_deg",
            "range_to_satellite_km",
            "range_to_satellite_uncertainty_km",
            "range_rate_of_satellite_km_per_sec",
            "range_rate_of_satellite_uncertainty_km_per_sec",
            "comments",
            "data_archive_link",
        ]
    )

    for i in range(1, 10):
        cat_id = str(i).zfill(5)
        writer.writerow(
            [
                "STARLINK-" + str(i),
                cat_id,
                "2024-01-02T23:59:59.123Z",
                0.01,
                8.1,
                0.01,
                33,
                -117,
                100,
                "none",
                "VISUAL",
                "CLEAR",
                "abc@test.com",
                "0123-4567-8910-1112",
                359.1234,
                0.01,
                -40.1234,
                0.03,
                560.123,
                5,
                3.123,
                0.01,
                None,
                None,
            ]
        )
