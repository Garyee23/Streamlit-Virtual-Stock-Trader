import requests
import xmltodict
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import urllib3
import sqlite3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 오류코드 삭제


# ------------------------------------ 데이터 관련 ------------------------------------

url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/" \
      "getStockPriceInfo?" \
      "serviceKey=nwFe1iYXo5NL2z6yTKP2KjBGMP66OS5yhSLhL6P4Flb2k5bxzK%2F9cITnYVX%2BdHqysj8JUFZkZ6giylrVfeJ9eQ%3D%3D&" \
      "numOfRows=10000&" \
      "pageNo=1&" \
      f"beginBasDt=20221001&" \
      "itmsNm=삼성전자"

response = requests.get(url, verify=False)
response = response.content

xmlobject = xmltodict.parse(response)
dict_data = xmlobject['response']['body']['items']['item']

df = pd.DataFrame(dict_data)

df.drop(['isinCd'], axis=1, inplace=True)
df.drop(['mkp'], axis=1, inplace=True)
df.drop(['trPrc'], axis=1, inplace=True)
df.drop(['lstgStCnt'], axis=1, inplace=True)
df.drop(['mrktTotAmt'], axis=1, inplace=True)

df = df.sort_index(ascending=False)
df = df.reset_index(drop=True)

# ------------------------------------ 기타 설정 ------------------------------------

plt.rc('font', family='Malgun Gothic')  # plt 글꼴설정

st.set_page_config(
    page_title='모의투자',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state="collapsed"
)

if 'count' not in st.session_state:
    st.session_state.count = 0


def increment_counter(increment_value=0):
    st.session_state.count += increment_value


def decrement_counter(decrement_value=0):
    st.session_state.count -= decrement_value

# ------------------------------------ database ------------------------------------

con = sqlite3.connect('stock.db')
curr = con.cursor()

money_df = pd.DataFrame({'구매금액': [], '구매수량': []})
money_df_list = []

# ------------------------------------ 변수들 ------------------------------------

stock = df.loc[st.session_state.count]  # 현재 선택된 주식

vsper = stock['fltRt']  # 전일대비등락률

high = stock['hipr']  # 고가

low = stock['lopr']  # 저가

vsnum = stock['vs']  # 전일대비등락가격

cur = stock['clpr']  # 현재가

tod = stock['basDt']  # 현재 날짜

chstock = df.astype({'basDt': 'int'})
chstock = df.astype({'clpr': 'int'})
chstock['price'] = chstock['clpr']

seedmoney = 1000000  # 주식 시드머니(시작머니, 현재 100만원)

# ------------------------------------ 수익계산관련 ------------------------------------

query = curr.execute("SELECT * From user") #DB값 전체선택
cols = [column[0] for column in query.description] #컬럼생성

money_info = pd.DataFrame.from_records(data=query.fetchall(), columns=cols) #DB값으로 수익관련 DataFrame 생성
st.dataframe(money_info)

buysum = money_info['총매수금액'].sum()  # 총 매수금액
st.write("총 매수금액 :", buysum)

numsum = money_info['총매수량'].sum()  # 총 매수량
st.write("총 매수량 :", numsum)


if buysum == 0 or numsum == 0:
    평단가 = 0
else:
    평단가 = int(buysum / numsum)
    st.write("현재 평단가 :",평단가)

매수가능금액 = seedmoney - buysum

현재평가금액 = int(cur) * numsum

손익 = 현재평가금액 - buysum

수익률 = (손익 / buysum) * 100

# ------------------------------------ streamlit ------------------------------------

menu = st.sidebar.selectbox('MENU', options=['현재가', '로그인', '회원가입', '정보수정'])

if menu == '현재가':

    if vsper[0] == '.':
        st.metric(label="현재가", value=cur + "원", delta='0' + vsper + "%")
        st.write('전일대비등락률은 :', '0' + vsper)
    elif vsper[0:2] == '-.':
        vsper = vsper.replace('-', '')
        st.metric(label="현재가", value=cur + "원", delta='-0' + vsper + "%")
        st.write('전일대비등락률은 :', '-0' + vsper)
    else:
        st.metric(label="현재가", value=cur + "원", delta=vsper + "%")
        st.write('전일대비등락률은 :', vsper)

    st.button('다음날짜', on_click=increment_counter,
              kwargs=dict(increment_value=1))

    st.button('이전날짜', on_click=decrement_counter,
              kwargs=dict(decrement_value=1))

    st.write('현재 인덱스 = ', st.session_state.count)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write('저가는 :', low)
        st.write('고가는 :', high)
        st.write('전일대비등락은 :', vsnum)
        st.write('현재날자는 :', tod)
        st.write('현재가격은 :', cur)

    with col2:
        plt.title('삼성전자')
        plt.plot(chstock.loc[:st.session_state.count, 'basDt'], chstock.loc[:st.session_state.count, 'price'], '.-',
                 color='black', )
        plt.grid(True, linestyle='--', color='#DDDDDD')
        plt.set_loglevel('WARNING')  # 오류코드 삭제
        st.pyplot(plt)

    with col3:
        Buynum = st.number_input('매수할 수량을 입력하세요.', min_value=1, step=1)  # 매수 수량입력
        Buybtn = st.button("매수하기")
        buyprice = int(cur) * Buynum
        st.write("구매가격은 :",buyprice)
        if Buybtn:
            if (매수가능금액 > 0):
                curr.execute(f"INSERT INTO user(총매수금액, 총매수량)"
                            f"VALUES({buyprice},{Buynum})")
                con.commit()
            else:
                st.markdown("매수가능금액을 초과하였습니다.")
        st.write("현재매수가능금액 :",매수가능금액)

    
    st.write(수익률)

    