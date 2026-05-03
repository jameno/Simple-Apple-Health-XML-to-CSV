<img style="height: 150px;" src="img/logo.png">

# Simple Apple Health XML to CSV

A small Python script that converts the `export.xml` file from your Apple
Health export into a single CSV.

## Get your data out of Apple Health

In the iPhone Health app, tap your profile icon → **Export All Health Data**.
Transfer the resulting `export.zip` to your computer.

| Health home | ➡️ | Export Data |
|--|--|--|
| <img src="img/health_home.jpg" width=300> || <img src="img/export_data_button.jpg" width=300> |

## Run the script

```
python3 apple_health_xml_convert.py
```

With no arguments, it looks for `export.zip`, `apple_health_export/export.xml`,
or `export.xml` in the current directory and writes
`apple_health_export_YYYY-MM-DD.csv` next to it.

To point at a specific file or change the output path:

```
python3 apple_health_xml_convert.py --input ~/Downloads/export.zip
python3 apple_health_xml_convert.py --output ~/health.csv
python3 apple_health_xml_convert.py -i path/to/export.zip -o out.csv
```

The input can be `export.zip`, `export.xml`, or the unzipped
`apple_health_export/` folder. Python 3.8+ is required; no third-party
dependencies.

In Excel the output looks something like this:

<img src="img/example_output.jpg">

## Notes

- The `HKQuantityTypeIdentifier`, `HKCategoryTypeIdentifier`, and
  `HKCharacteristicTypeIdentifier` prefixes are stripped from `type` values
  and column names for legibility.
- Rows are written in document order (roughly chronological). If you want
  them sorted by date, sort the CSV with your tool of choice (e.g. `sort` or
  pandas).
- Memory stays bounded regardless of export size, so multi-GB exports work
  on modest hardware.

## License

BSD 2-Clause — see [LICENSE.md](LICENSE.md).
