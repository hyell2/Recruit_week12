
import streamlit as st
import pandas as pd
import plotly.express as px
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os


# 크롤링 함수
def load_data():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")

    # 잡코리아 크롤링
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_url = "https://www.jobkorea.co.kr/Search/?stext=데이터분석"
    driver.get(search_url)
    time.sleep(3)

    job_list = []
    for i in range(2, 20):
        try:
            xpath = f'//*[@id="jk-«R1h7alqdb»-content-recruit"]/div/div/div[{i}]/div'
            title_element = driver.find_element(By.XPATH, xpath)
            lines = title_element.text.split('\n')

            link_xpath = f'//*[@id="jk-«R1h7alqdb»-content-recruit"]/div/div/div[{i}]/div//a'
            link_element = driver.find_element(By.XPATH, link_xpath)
            link_url = link_element.get_attribute("href")

            if len(lines) >= 4:
                company_name = lines[2]
                job_title = lines[3]
                details = ', '.join(lines[4:-1])

                job_list.append({
                    "Site": "Job_Korea",
                    "Col_Company": company_name,
                    "Col_Recruit": job_title,
                    "Col_detail": details,
                    "Col_url": link_url
                })
            else:
                print(f"[{i}] 정보가 충분하지 않음")
        except Exception as e:
            print(f"[{i}] 제목 없음 또는 XPath 실패")

    jobkorea_df = pd.DataFrame(job_list)
    driver.quit()

    # 사람인 크롤링
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        search_url = "https://www.saramin.co.kr/zf_user/search/recruit?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword=데이터분석&recruitPage=1&recruitSort=relation&recruitPageCount=40"
        driver.get(search_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.item_recruit"))
        )

        job_list = []
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.item_recruit")

        for card in job_cards:
            try:
                title_element = card.find_element(By.CSS_SELECTOR, "h2.job_tit > a[title]")
                job_title = title_element.get_attribute("title")
                job_link = title_element.get_attribute("href")

                company_element = card.find_element(By.CSS_SELECTOR, "strong.corp_name > a.track_event.data_layer")
                company_name = company_element.text

                condition_spans = card.find_elements(By.CSS_SELECTOR, "div.job_condition > span")
                details = ', '.join([span.text for span in condition_spans if span.text.strip()])

                job_list.append({
                    "Site": "Saramin",
                    "Col_Company": company_name,
                    "Col_Recruit": job_title,
                    "Col_detail": details,
                    "Col_url": job_link
                })

            except Exception as e:
                print(f"[공고 누락] 오류 발생: {e}")
                continue

        saramin_df = pd.DataFrame(job_list)
        driver.quit()

    except (TimeoutException, WebDriverException) as e:
        print(f"사람인 크롤링 실패: {e}")
        saramin_df = pd.DataFrame()

    # 합치기
    df_total = pd.concat([jobkorea_df, saramin_df], ignore_index=True)
    df_total.to_csv("recruit_data.csv", index=False, encoding="utf-8-sig")
    return df_total


# ratio
def get_site_ratio(df_total):
    site_counts = df_total["Site"].value_counts().reset_index()
    site_counts.columns = ["Site", "Count"]
    total_count = site_counts["Count"].sum()
    site_counts["Ratio"] = (site_counts["Count"] / total_count * 100).round(2)
    return site_counts





# Streamlit
# 페이지 설정
st.set_page_config(page_title="Title")
st.title("Title")

# 버튼 클릭 시 실행
if st.button("Recruit Searching"):

    if os.path.exists("recruit_data.csv"):
        df_total = pd.read_csv("recruit_data.csv", encoding="utf-8-sig")
    else:
        df_total = load_data()

    # 크롤링 데이터
    st.dataframe(df_total, use_container_width=True)

    # ratio 
    site_counts = get_site_ratio(df_total)
    st.dataframe(site_counts)


    # 파이차트 그리기
    fig = px.pie(
        site_counts,
        title="Recruitment Ratio",
        names="Site",
        values="Ratio" #도넛 차트로 바꾸려면 0.4 정도로 설정
    )
    st.plotly_chart(fig, use_container_width=True)
