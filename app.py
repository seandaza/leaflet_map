from flask import Flask, request
import folium
import pandas as pd
import geopandas as gpd
import requests
import os
import numpy as np
import branca

PROJ_DIR = os.path.abspath(os.path.join(os.pardir))
nombre_dir_pre = os.path.join(PROJ_DIR, "data", "raw")
processed_data_dir = os.path.join(PROJ_DIR, "data", "processed")

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    datab = pd.read_csv("final_dnb_datasetV3.csv")

    datab = datab.replace('-', np.nan)

    datab = datab.drop("Unnamed: 0", axis=1)

    datab = datab.dropna(subset="latitude")

    typos_col = {
        "latitude": 'float64', 
        'longitude': 'float64'
    }

    datab = datab.astype(typos_col)

    records = datab.copy()  # Copiar todos los datos

    records = records.dropna(subset=["latitude"])

    records = records.replace('-', np.nan)

    records = records.dropna()

    records = records.astype(typos_col)

    mapx = folium.Map(location=[18.40557, -93.20114], zoom_start=4)

    def popup_html(index, dataf):
        company_name = dataf.loc[index, "name"]
        company_address = dataf.loc[index, "Address"]
        company_industry = dataf.loc[index, 'industry']
        company_trajectory = dataf.loc[index, 'growth_trajectory']
        company_employees = dataf.loc[index, 'Emp_total']
        company_cap = dataf.loc[index, "Capacity_Status"]
        company_cap_score = dataf.loc[index, 'Capacity_Score']
        company_sales = dataf.loc[index, 'sales_(Thousands of USD)']
        company_rfc = dataf.loc[index, 'Lead_rfc']
        company_rank = dataf.loc[index, 'Rank']

        left_col_color = "#19a7bd"
        right_col_color = "#f2f0d3"

        html = """<!DOCTYPE html>
        <html>
        <head>
        <h4 style="margin-bottom:10"; width="200px">{}</h4>""".format(company_name) + """
        </head>
            <table style="height: 126px; width: 350px;">
        <tbody>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">RFC</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_rfc) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Industry</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_industry) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Address</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_address) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Average number of employees</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_employees) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Growth Trajectory</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_trajectory) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Debt Status</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_cap) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Debt Capacity Score</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_cap_score) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Average yearly sales (Thousands of USD)</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_sales) + """
        </tr>
        <tr>
        <td style="background-color: """ + left_col_color + """;"><span style="color: #ffffff;">Lead Rank</span></td>
        <td style="width: 150px;background-color: """ + right_col_color + """;">{}</td>""".format(company_rank) + """
        </tr>
        </tbody>
        </table>
        </html>
        """
        return html

    filtered_records = None

    if request.method == 'POST':
        selected_filter = request.form.get('filter')
        if selected_filter == 'rank':
            min_rank = int(request.form.get('min_rank'))
            max_rank = int(request.form.get('max_rank'))
            filtered_records = records[(records['Rank'] >= min_rank) & (records['Rank'] <= max_rank)]
            print(filtered_records)  # Imprime el DataFrame filtrado

    for index, row in datab.iterrows():
        coords = (row["latitude"], row["longitude"])
        if filtered_records is None or index in filtered_records.index:
            html = popup_html(index, datab)
            iframe = branca.element.IFrame(html=html, width=300, height=280)
            popup = folium.Popup(folium.Html(html, script=True), max_width=300)
            folium.Marker(coords, popup=popup).add_to(mapx)

    filters = {
        'rank': 'Rank',
    }

    filter_options = ''.join('<option value="{}">{}</option>'.format(key, value) for key, value in filters.items())

    #filter_options = ''.join(f'<option value="{key}">{value}</option>' for key, value in filters.items())

    html = """
        <!DOCTYPE html>
        <html>
        <body>
        <form method="POST" action="/">
            <label for="filter">Select Filter:</label>
            <select id="filter" name="filter">
                {filter_options}
            </select>
            <br><br>
            <label for="min_rank">Minimum Rank:</label>
            <input type="number" id="min_rank" name="min_rank">
            <br><br>
            <label for="max_rank">Maximum Rank:</label>
            <input type="number" id="max_rank" name="max_rank">
            <br><br>
            <input type="submit" value="Apply Filter">
        </form>
        </body>
        </html>
    """.format(filter_options=filter_options)

    return html + mapx.get_root().render()


if __name__ == "__main__":
    app.run()
