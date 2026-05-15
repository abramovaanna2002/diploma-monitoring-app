import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Исследование устойчивости туристических кластеров", layout="wide")

DATA_DIR = Path("data")
IMAGES_DIR = Path("images")

IMAGE_NAMES = {
    "olkhon": ["olkhon", "ольхон"],
    "curonian_spit": ["curonian_spit", "curonian", "kurshskaya_kosa", "куршская_коса"],
    "elbrus": ["elbrus", "prielbrusie", "приэльбрусье"],
}

TERRITORY_INFO = {
    "olkhon": (
        "Ольхон - островная туристическая территория Байкала с сочетанием степных, "
        "лесостепных и прибрежных ландшафтов. По данным системы Baikalpass, за январь-июнь "
        "2025 года было оформлено 102 167 разрешений на посещение Прибайкальского национального "
        "парка, что на 12% больше аналогичного периода предыдущего года. Для анализа учитываются "
        "участки поселенческой застройки, дороги, прибрежные зоны и места концентрации туристов."
    ),
    "curonian_spit": (
        "Куршская коса - узкая прибрежная территория между Балтийским морем и Куршским заливом. "
        "По данным Минприроды России, национальный парк «Куршская коса» входил в число лидеров "
        "по посещаемости среди ООПТ и принял около 886 тыс. посетителей. Территория сочетает "
        "лесные массивы, пляжи и дюнные комплексы, поэтому показатели открытых поверхностей "
        "требуют осторожной интерпретации."
    ),
    "elbrus": (
        "Приэльбрусье - горный туристический кластер с выраженной инфраструктурой в районе "
        "Терскола, Азау, Чегета, канатных дорог и горнолыжных склонов. Курорт «Эльбрус» в 2024 году "
        "принял около 818 тыс. посетителей, из них около 300 тыс. пришлось на летний период. "
        "Антропогенная нагрузка здесь проявляется локально и связана с трассами, дорогами, "
        "подъёмниками и зонами концентрации отдыхающих."
    ),
}

COLUMN_RENAME = {
    "year": "Год",
    "name": "Код объекта",
    "name_ru": "Объект",
    "type": "Тип территории",
    "region": "Регион",

    "NDVI_mean": "Средний NDVI",
    "NDBI_mean": "Средний NDBI",
    "BSI_mean": "Средний BSI",

    "NDVI_diff_2025_2019": "Изменение NDVI, 2025-2019",
    "NDBI_diff_2025_2019": "Изменение NDBI, 2025-2019",
    "BSI_diff_2025_2019": "Изменение BSI, 2025-2019",

    "total_area_km2": "Площадь полигона, км²",
    "NDVI_loss_area_km2": "Площадь снижения NDVI, км²",
    "NDVI_loss_percent": "Доля снижения NDVI, %",
    "NDBI_growth_area_km2": "Площадь роста NDBI, км²",
    "NDBI_growth_percent": "Доля роста NDBI, %",
    "BSI_growth_area_km2": "Площадь роста BSI, км²",
    "BSI_growth_percent": "Доля роста BSI, %",
    "degradation_risk_area_km2": "Площадь комплексных зон риска, км²",
    "degradation_risk_percent": "Доля комплексных зон риска, %",

    "SI_base_mean": "Базовый индекс устойчивости",
    "SI_RF_mean": "Адаптивный индекс устойчивости",
    "risk_percent": "Доля комплексных зон риска, %",
    "SI_base_final": "Базовый индекс с учётом риска",
    "SI_RF_final": "Итоговый адаптивный индекс",
    "SI_RF_final_class": "Итоговый класс устойчивости",
}


def display_table(df, columns=None):
    """Return dataframe with Russian column names for display."""
    result = df.copy()
    if columns is not None:
        result = result[columns].copy()
    return result.rename(columns=COLUMN_RENAME)


@st.cache_data
def load_data():
    indices = pd.read_csv(DATA_DIR / "tourism_clusters_indices_2019_2021_2025.csv")
    changes = pd.read_csv(DATA_DIR / "tourism_clusters_index_changes_2025_2019.csv")
    risk = pd.read_csv(DATA_DIR / "risk_zones_2025_2019_combined.csv")
    final = pd.read_csv(DATA_DIR / "tourism_clusters_rf_sustainability_index_2025.csv")

    for df in [indices, changes, risk, final]:
        for col in [".geo", "system:index"]:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

    numeric_cols = [
        "year",
        "NDVI_mean", "NDBI_mean", "BSI_mean",
        "NDVI_diff_2025_2019", "NDBI_diff_2025_2019", "BSI_diff_2025_2019",
        "total_area_km2", "NDVI_loss_area_km2", "NDVI_loss_percent",
        "NDBI_growth_area_km2", "NDBI_growth_percent",
        "BSI_growth_area_km2", "BSI_growth_percent",
        "degradation_risk_area_km2", "degradation_risk_percent",
        "SI_base_mean", "SI_RF_mean", "risk_percent",
        "SI_base_final", "SI_RF_final",
    ]

    for df in [indices, changes, risk, final]:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    return indices, changes, risk, final


def find_image(name: str):
    if not IMAGES_DIR.exists():
        return None

    for stem in IMAGE_NAMES.get(name, [name]):
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            candidate = IMAGES_DIR / f"{stem}{ext}"
            if candidate.exists():
                return candidate
    return None


def interpretation(row):
    final_class = row["SI_RF_final_class"]
    risk_value = float(row["risk_percent"])

    if final_class == "высокая устойчивость" and risk_value < 5:
        return (
            "Территория характеризуется высоким уровнем устойчивости. "
            "Доля комплексных зон риска невелика, поэтому локальные изменения "
            "не оказывают существенного влияния на итоговую оценку."
        )

    if final_class == "высокая устойчивость":
        return (
            "Территория сохраняет высокий класс устойчивости, однако доля зон риска заметна. "
            "Требуется локальный мониторинг участков туристической инфраструктуры и зон повышенной рекреационной нагрузки."
        )

    if final_class == "средняя устойчивость":
        return (
            "Территория относится к классу средней устойчивости. Общее состояние не является критическим, "
            "однако локальные зоны потенциальной деградации заметно влияют на итоговый индекс."
        )

    return (
        "Территория относится к классу низкой устойчивости. Необходима детальная проверка локальных зон риска "
        "и разработка мер по снижению антропогенной нагрузки."
    )


def risk_analysis_text(name: str, row):
    ndvi_loss = float(row["NDVI_loss_percent"])
    ndbi_growth = float(row["NDBI_growth_percent"])
    bsi_growth = float(row["BSI_growth_percent"])
    complex_risk = float(row["degradation_risk_percent"])
    complex_area = float(row["degradation_risk_area_km2"])

    base_text = (
        f"Комплексные зоны риска занимают {complex_area:.2f} км², или {complex_risk:.2f}% площади полигона. "
        f"Снижение NDVI выявлено на {ndvi_loss:.2f}% территории, рост NDBI - на {ndbi_growth:.2f}%, "
        f"рост BSI - на {bsi_growth:.2f}%."
    )

    if name == "olkhon":
        return (
            base_text + " Для Ольхона это указывает на заметную локальную неоднородность: "
            "часть территории сохраняет стабильное состояние, но отдельные участки демонстрируют сочетание "
            "снижения растительности и роста признаков открытых или инфраструктурно трансформированных поверхностей. "
            "Такие зоны целесообразно дополнительно сопоставлять с дорогами, прибрежными участками, окрестностями "
            "населённых пунктов и популярными туристическими маршрутами. При интерпретации BSI нужно учитывать "
            "естественные степные и сухие ландшафты острова."
        )

    if name == "curonian_spit":
        return (
            base_text + " Для Куршской косы доля комплексных зон риска минимальна среди трёх объектов. "
            "Это согласуется с положительной динамикой NDVI и снижением средних значений NDBI и BSI. "
            "Выявленные участки риска имеют локальный характер. Их следует рассматривать с учётом природной специфики "
            "косы, где песчаные и дюнные поверхности являются естественным элементом ландшафта, а не всегда признаком деградации."
        )

    if name == "elbrus":
        return (
            base_text + " Для Приэльбрусья доля комплексных зон риска является наиболее высокой. "
            "Это отражает локальный характер нагрузки в горном туристическом кластере: изменения концентрируются "
            "вблизи Азау, Терскола, Чегета, канатных дорог, трасс, склонов и транспортных коридоров. "
            "Даже при сравнительно небольшой абсолютной площади такие участки заметно влияют на итоговую оценку, "
            "поскольку сам полигон охватывает компактное ядро туристического освоения."
        )

    return base_text


def final_analysis_text(name: str, row):
    si_base = float(row["SI_base_mean"])
    si_rf = float(row["SI_RF_mean"])
    si_base_final = float(row["SI_base_final"])
    si_rf_final = float(row["SI_RF_final"])
    risk = float(row["risk_percent"])
    final_class = row["SI_RF_final_class"]

    base_text = (
        f"Базовый индекс устойчивости за 2025 год составляет {si_base:.4f}, "
        f"адаптивный индекс Random Forest - {si_rf:.4f}. После учёта доли комплексных зон риска "
        f"({risk:.2f}%) итоговый адаптивный индекс равен {si_rf_final:.4f}. "
        f"Итоговый класс: {final_class}."
    )

    if name == "olkhon":
        return (
            base_text + " У Ольхона адаптивный индекс немного выше базового, поскольку модель Random Forest "
            "увеличила вклад NDVI. Однако корректировка на зоны риска снижает итоговую оценку до класса средней устойчивости. "
            "Это показывает, что общая картина по острову не является критической, но локальные очаги нагрузки достаточно велики, "
            "чтобы влиять на итоговую классификацию."
        )

    if name == "curonian_spit":
        return (
            base_text + " Куршская коса сохраняет высокий класс устойчивости как до, так и после корректировки. "
            "Низкая доля зон риска почти не снижает итоговый индекс. Этот результат показывает, что в пределах выбранного полигона "
            "общая структура растительного покрова и состояние поверхности остаются наиболее благоприятными среди исследуемых объектов."
        )

    if name == "elbrus":
        return (
            base_text + " Приэльбрусье сохраняет высокий класс по адаптивной модели, но значение находится близко к порогу 0,60. "
            "Поэтому результат следует трактовать как погранично высокий уровень устойчивости. Средняя оценка остаётся благоприятной, "
            "но высокая доля локальных зон риска показывает необходимость регулярного мониторинга территории вокруг ключевых элементов "
            "туристической инфраструктуры."
        )

    return base_text


indices, changes, risk, final = load_data()

st.title("Исследование устойчивости туристических кластеров России")
st.caption(
    "Демонстрационное веб-приложение на основе Sentinel-2A/B, индексов NDVI, NDBI, BSI, "
    "зон риска и интегрального индекса устойчивости."
)

objects = final["name_ru"].tolist()
selected_ru = st.sidebar.selectbox("Выберите туристический кластер", objects)
selected_row = final[final["name_ru"] == selected_ru].iloc[0]
selected_name = selected_row["name"]

idx_obj = indices[indices["name"] == selected_name].copy()
changes_obj = changes[changes["name"] == selected_name].copy()
risk_obj = risk[risk["name"] == selected_name].copy()
final_obj = final[final["name"] == selected_name].copy()

st.sidebar.markdown("### Период анализа")
st.sidebar.write("Базовый период: **2019**")
st.sidebar.write("Промежуточный этап: **2021**")
st.sidebar.write("Последний анализируемый год: **2025**")
st.sidebar.markdown("### Источник данных")
st.sidebar.write("Sentinel-2A/B")
st.sidebar.write("Сезон: 1 июня - 30 сентября")

st.sidebar.markdown("### Отображение")
image_width = st.sidebar.slider(
    "Ширина изображения, пикс.",
    min_value=300,
    max_value=1000,
    value=650,
    step=50
)

tab_overview, tab_indices, tab_dynamic, tab_risk, tab_final, tab_compare, tab_method = st.tabs(
    [
        "Обзор",
        "Индексы",
        "Динамика 2025-2019",
        "Зоны риска",
        "Итоговая оценка",
        "Сравнение объектов",
        "Методика",
    ]
)

with tab_overview:
    st.header(selected_ru)

    info_col, image_col = st.columns([1.15, 2.2])

    with info_col:
        st.markdown("### Краткая характеристика территории")
        st.write(TERRITORY_INFO.get(selected_name, "Описание территории не задано."))
        st.markdown("### Параметры анализа")
        st.write("Период сравнения: **2019-2025 гг.**")
        st.write("Опорные годы: **2019, 2021, 2025**")
        st.write("Сезон: **1 июня - 30 сентября**")

    with image_col:
        image_path = find_image(selected_name)
        if image_path:
            st.image(str(image_path), caption=selected_ru, width=image_width)
        else:
            st.info(
                "Изображение не найдено. Создайте папку images и добавьте файл, например: "
                "olkhon.jpg, curonian_spit.jpg или elbrus.jpg."
            )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SI_RF 2025", f"{float(selected_row['SI_RF_mean']):.4f}")
    c2.metric("SI_RF_final", f"{float(selected_row['SI_RF_final']):.4f}")
    c3.metric("Зоны риска", f"{float(selected_row['risk_percent']):.2f}%")
    c4.metric("Класс", selected_row["SI_RF_final_class"])

    st.markdown("### Краткая интерпретация")
    st.info(interpretation(selected_row))

with tab_indices:
    st.subheader("Средние значения NDVI, NDBI и BSI")

    long_idx = idx_obj.melt(
        id_vars=["year", "name_ru"],
        value_vars=["NDVI_mean", "NDBI_mean", "BSI_mean"],
        var_name="Индекс",
        value_name="Значение",
    )
    long_idx["Индекс"] = long_idx["Индекс"].map({
        "NDVI_mean": "Средний NDVI",
        "NDBI_mean": "Средний NDBI",
        "BSI_mean": "Средний BSI"
    })

    chart = (
        alt.Chart(long_idx)
        .mark_line(point=True)
        .encode(
            x=alt.X("year:O", title="Год"),
            y=alt.Y("Значение:Q", title="Среднее значение"),
            color=alt.Color("Индекс:N", title="Показатель"),
            tooltip=["year", "Индекс", alt.Tooltip("Значение:Q", format=".4f")],
        )
        .properties(height=380)
    )

    st.altair_chart(chart, use_container_width=True)
    st.dataframe(
        display_table(idx_obj, ["year", "NDVI_mean", "NDBI_mean", "BSI_mean"]),
        use_container_width=True
    )

with tab_dynamic:
    st.subheader("Изменения индексов за период 2019-2025 гг.")

    diff_cols = ["NDVI_diff_2025_2019", "NDBI_diff_2025_2019", "BSI_diff_2025_2019"]
    diff_data = changes_obj[diff_cols].T.reset_index()
    diff_data.columns = ["Показатель", "Значение"]
    diff_data["Показатель"] = diff_data["Показатель"].map({
        "NDVI_diff_2025_2019": "Изменение NDVI",
        "NDBI_diff_2025_2019": "Изменение NDBI",
        "BSI_diff_2025_2019": "Изменение BSI"
    })

    chart = (
        alt.Chart(diff_data)
        .mark_bar()
        .encode(
            x=alt.X("Показатель:N", title="Показатель"),
            y=alt.Y("Значение:Q", title="Изменение"),
            tooltip=["Показатель", alt.Tooltip("Значение:Q", format=".4f")],
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)
    st.dataframe(
        display_table(changes_obj, diff_cols),
        use_container_width=True
    )

with tab_risk:
    st.subheader("Локальные зоны потенциальной деградации")

    risk_cols = [
        "NDVI_loss_percent",
        "NDBI_growth_percent",
        "BSI_growth_percent",
        "degradation_risk_percent",
    ]
    risk_labels = {
        "NDVI_loss_percent": "Снижение NDVI",
        "NDBI_growth_percent": "Рост NDBI",
        "BSI_growth_percent": "Рост BSI",
        "degradation_risk_percent": "Комплексные зоны риска",
    }

    risk_data = risk_obj[risk_cols].T.reset_index()
    risk_data.columns = ["Показатель", "Доля, %"]
    risk_data["Показатель"] = risk_data["Показатель"].map(risk_labels)

    chart = (
        alt.Chart(risk_data)
        .mark_bar()
        .encode(
            x=alt.X("Показатель:N", title="Тип зоны"),
            y=alt.Y("Доля, %:Q", title="Доля территории, %"),
            tooltip=["Показатель", alt.Tooltip("Доля, %:Q", format=".2f")],
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)
    st.dataframe(
        display_table(
            risk_obj,
            [
                "total_area_km2",
                "NDVI_loss_area_km2",
                "NDVI_loss_percent",
                "NDBI_growth_area_km2",
                "NDBI_growth_percent",
                "BSI_growth_area_km2",
                "BSI_growth_percent",
                "degradation_risk_area_km2",
                "degradation_risk_percent",
            ]
        ),
        use_container_width=True,
    )

    st.markdown("### Вывод по зонам риска")
    st.write(risk_analysis_text(selected_name, risk_obj.iloc[0]))

with tab_final:
    st.subheader("Итоговая оценка устойчивости за 2025 г.")

    cols = [
        "SI_base_mean",
        "SI_RF_mean",
        "risk_percent",
        "SI_base_final",
        "SI_RF_final",
        "SI_RF_final_class",
    ]

    st.dataframe(
        display_table(final_obj, cols),
        use_container_width=True
    )

    si_data = pd.DataFrame(
        {
            "Показатель": [
                "Базовый индекс",
                "Адаптивный индекс",
                "Базовый индекс с учётом риска",
                "Итоговый адаптивный индекс"
            ],
            "Значение": [
                float(selected_row["SI_base_mean"]),
                float(selected_row["SI_RF_mean"]),
                float(selected_row["SI_base_final"]),
                float(selected_row["SI_RF_final"]),
            ],
        }
    )

    chart = (
        alt.Chart(si_data)
        .mark_bar()
        .encode(
            x=alt.X("Показатель:N", title="Индекс"),
            y=alt.Y("Значение:Q", title="Значение", scale=alt.Scale(domain=[0, 1])),
            tooltip=["Показатель", alt.Tooltip("Значение:Q", format=".4f")],
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### Автоматическая интерпретация")
    st.info(interpretation(selected_row))

    st.markdown("### Подробный вывод по итоговой оценке")
    st.write(final_analysis_text(selected_name, selected_row))

with tab_compare:
    st.subheader("Сравнение исследуемых туристических кластеров")

    comparison_cols = [
        "name_ru",
        "SI_base_mean",
        "SI_RF_mean",
        "risk_percent",
        "SI_base_final",
        "SI_RF_final",
        "SI_RF_final_class",
    ]

    st.dataframe(
        display_table(final, comparison_cols),
        use_container_width=True,
        height=150
    )

    st.markdown("### Доля комплексных зон риска")
    risk_chart = (
        alt.Chart(final)
        .mark_bar()
        .encode(
            x=alt.X("name_ru:N", title="Объект"),
            y=alt.Y("risk_percent:Q", title="Доля зон риска, %"),
            tooltip=[
                alt.Tooltip("name_ru:N", title="Объект"),
                alt.Tooltip("risk_percent:Q", title="Зоны риска, %", format=".2f"),
                alt.Tooltip("SI_RF_final:Q", title="SI_RF_final", format=".4f"),
                alt.Tooltip("SI_RF_final_class:N", title="Класс"),
            ],
        )
        .properties(height=360)
    )

    st.altair_chart(risk_chart, use_container_width=True)

    st.markdown("### Сравнительный вывод")
    st.write(
        "Сравнение объектов показывает, что наиболее устойчивое состояние характерно для Куршской косы. "
        "Она имеет высокий итоговый адаптивный индекс и минимальную долю комплексных зон риска. "
        "Ольхон относится к средней устойчивости, поскольку локальные зоны риска заметно снижают итоговую оценку. "
        "Приэльбрусье сохраняет высокий класс устойчивости по итоговому адаптивному индексу, но находится близко к пороговой границе. "
        "Для него требуется регулярный локальный мониторинг участков туристической инфраструктуры, склонов, дорог и зон концентрации отдыхающих."
    )

with tab_method:
    st.subheader("Методика расчёта")

    st.markdown(
        r"""
### 1. Спутниковые данные

Для анализа использованы сезонные медианные композиты Sentinel-2 за летний период с 1 июня по 30 сентября. 
Опорные годы исследования: 2019, 2021 и 2025. Данные предварительно фильтровались по облачности, после чего выполнялось маскирование облаков, теней, воды и снежно-ледовых поверхностей.

### 2. Спектральные индексы

**NDVI** используется для оценки состояния растительного покрова:

$$
NDVI = \frac{NIR - RED}{NIR + RED}
$$

**NDBI** используется как индикатор застроенных, инфраструктурных и минеральных поверхностей:

$$
NDBI = \frac{SWIR - NIR}{SWIR + NIR}
$$

**BSI** используется для оценки открытых почв и оголённых поверхностей:

$$
BSI = \frac{(SWIR + RED) - (NIR + BLUE)}{(SWIR + RED) + (NIR + BLUE)}
$$

### 3. Нормализация

$$
Index_{norm} = \frac{Index + 1}{2}
$$

### 4. Базовый индекс устойчивости

$$
SI_{base} = 0.4 \cdot NDVI_{norm} + 0.3 \cdot (1 - NDBI_{norm}) + 0.3 \cdot (1 - BSI_{norm})
$$

### 5. Адаптивный индекс на основе Random Forest

После оценки значимости признаков методом Random Forest веса были уточнены:

$$
SI_{RF} = 0.444 \cdot NDVI_{norm} + 0.297 \cdot (1 - NDBI_{norm}) + 0.259 \cdot (1 - BSI_{norm})
$$

### 6. Комплексные зоны риска

Комплексная зона риска выделяется при одновременном выполнении условий:

$$
\Delta NDVI < -0.05
$$

и

$$
\Delta NDBI > 0.03 \quad \text{или} \quad \Delta BSI > 0.03
$$

### 7. Итоговый индекс с учётом зон риска

$$
SI_{final} = SI \cdot \left(1 - \frac{R}{100}\right)
$$

где \(R\) - доля комплексных зон риска в пределах полигона, %.

### 8. Интерпретация классов устойчивости

| Значение индекса | Класс устойчивости |
|---:|---|
| менее 0,40 | низкая устойчивость |
| 0,40-0,60 | средняя устойчивость |
| более 0,60 | высокая устойчивость |
"""
    )
