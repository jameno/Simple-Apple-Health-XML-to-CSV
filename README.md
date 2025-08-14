
<div align="right">
  <details>
    <summary >🌐 Language</summary>
    <div>
      <div align="center">
        <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=en">English</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=zh-CN">简体中文</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=zh-TW">繁體中文</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=ja">日本語</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=ko">한국어</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=hi">हिन्दी</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=th">ไทย</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=fr">Français</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=de">Deutsch</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=es">Español</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=it">Italiano</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=ru">Русский</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=pt">Português</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=nl">Nederlands</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=pl">Polski</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=ar">العربية</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=fa">فارسی</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=tr">Türkçe</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=vi">Tiếng Việt</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=id">Bahasa Indonesia</a>
        | <a href="https://openaitx.github.io/view.html?user=jameno&project=Simple-Apple-Health-XML-to-CSV&lang=as">অসমীয়া</
      </div>
    </div>
  </details>
</div>

# Simple Apple Health XML to CSV

A simple script to convert Apple Health's export.xml file to an easy to use csv.



## How to Run 

### 1. Verify you have Python 3 & Pandas installed on your machine or environment

`python --version` should return _Python 3.x.x_ where x is any number. 

If you have Python 2.x.x, please upgrade to Python 3 here: https://www.python.org/downloads/ (or specify your environment's Python version)

`python3 -c "import pandas"` should return blank from the command line

If you get a _**ModuleNotFoundError: No module named 'pandas'**_ error, install pandas and try again:

`pip3 install pandas`


### 2. Export your Apple Health Data

| Health Home | ➡️ | Export Data |
|--|--|--|
|<img style="float: left;" src="img/health_home.jpg" width=300>||<img style="float: left;" src="img/export_data_button.jpg" width = 300 >|

Your data will be prepared, and then you can transfer the export.zip file to your machine.

### 3. Unzip the file, which should contain:

   * apple_health_export
     * export.xml (This is the file with your data that you want to convert)
     
     * export_cda.xml
     
       

### 4. Place the "apple_health_xml_convert.py" file from this repo into the folder alongside the files and run the script

`python3 apple_health_xml_convert.py`



The export will be written with the format:

* **apple_health_export_YYYY-MM-DD.csv**

  

In Excel, the output should look something like this:

<img style="float: left;" src="img/example_output.jpg">

Note: This script removes the Apple Health data prefixes: `HKQuantityTypeIdentifier`, `HKCategoryTypeIdentifier`, and `HKCharacteristicTypeIdentifier` for increased legibility. Feel free to comment out those lines in the code with a `#` if you want to keep them in the CSV output.
