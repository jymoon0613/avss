import pandas as pd
import numpy as np

from bokeh.plotting import figure
from bokeh.io import output_file, show, curdoc
from bokeh.plotting import ColumnDataSource
from bokeh.driving import linear
from bokeh.layouts import column, row
from bokeh.models import (Range1d, ColumnDataSource, Toggle, Div, 
                          CustomJS, Select, CategoricalColorMapper, LabelSet, FactorRange)
from utils import data2seq, optimize
import tensorflow as tf 
from tensorflow import keras
from tensorflow.keras.models import model_from_json
import numpy as np
import pandas as pd

# 제목
html = """<h3>Real-time Voltage and Optimal Adjustment</h3>"""
div = Div(text=html, style={'font-size': '220%'}, width=1000, height=100)

# 데이터 준비
data = pd.read_csv('data/data.csv')
current_data = data.iloc[0:4]
stream_data = data.iloc[4:].reset_index(drop=True)
tap_target=0
cap_target=0
value = False

# 실시간 전압
source = ColumnDataSource(data=dict(x=[], y=[]))

# 최적화 조정방안(5개 일반 리액터, 1개 가변 리액터 따로 CDS 구성)
source2 = ColumnDataSource(data=dict(reactor=[], top=[], open_close=[]))
source3 = ColumnDataSource(data=dict(reactor=[], top=[], cap_target=[]))

# 현재 6개 리액터 작동 현황, 각 리액터별 작동 횟수 사전 정의
params_now = [1, 0, 0, 0, 1, 1]
n_used = [200, 150, 100, 50, 50, 100]

# 저장된 모델 불러오기
with open('model/model.json', 'r') as json_file:
    model = model_from_json(json_file.read())

# Line chart : 실시간 전압
plot = figure(height=500, width=1800, title="Real-time Voltage")
plot.title.text_font_size = '16pt'
plot.xaxis.axis_label = 'Time(s)'
plot.yaxis.axis_label = 'Voltage(kV)'

plot.line('x', 'y', source=source, line_width=1.0, line_color='red')
plot.circle('x', 'y', source=source, color='red', fill_color='white', size=5)

# Bar chart : 일반 리액터 투입 개방 여부
plot2 = figure(height=300, width=1000, title="Common Reactor Adjustment (Use:Green / Not Use:Red)", toolbar_location=None)
plot2.title.text_font_size = '16pt'
plot2.xaxis.axis_label = 'Common Reactor'
plot2.yaxis.axis_label = 'Whether to use it'

open_close_mapper = CategoricalColorMapper(factors = ['1.0', '0.0'], palette=['green', 'red'])
plot2.vbar(x='reactor', top='top', source=source2, width=0.7,
             color=dict(field='open_close', transform=open_close_mapper))

# Bar chart : 가변 리액터 tab 및 최종 투입용량
plot3 = figure(height=300, width=1000, title="Variable Reactor Tab levels and Optimal Input Capacity", 
               x_range=(0,20), y_range=FactorRange(factors=['1']), toolbar_location=None)
plot3.title.text_font_size = '16pt'
plot3.xaxis.axis_label = 'Variable Reactor Tab levels(0 ~ 18)'
plot3.yaxis.axis_label = 'Variable Reactor'

plot3.hbar(y='reactor', right='top', source=source3, height=0.4, fill_color='green')
plot3.text(x='top', y='reactor', source=source3, text='cap_target', color='white', text_align='center', text_font_size = {'value': '16px'})

# Streaming을 시작할 버튼 위젯 추가
toggle = Toggle(label = "Start", button_type = "success")

# 0부터 1씩 증가하며 주기적으로 input update
@linear(m=1, b=0)
def update(step):

    global current_data, params_now, n_used, value

    if toggle.active:
        volt = {
            'x':[step],
            'y':[stream_data.iloc[step]['volt']]
        }
        source.stream(volt, 10000)
        if step >= 19:
            plot.x_range.end = step
            plot.x_range.start = step - 20
        
        current_data = current_data.append(stream_data.iloc[step],ignore_index=True)
        if value:
            current_data.iloc[-2,2] = value
        
        sequence = data2seq(current_data, length = 4)
        pred_ = np.random.randint(200, 1068)
        # pred = model.predict(sequence)[0,0]
        # pred_ = np.round(pred * (1068.0 - 200.0) + 200.0, 1)

        list_open_close, cap_target, params_now_, n_used_ = optimize(pred_, params_now, n_used)

        value = cap_target
        n_used = n_used_
        params_now = params_now_

        list_open_close = [str(x) for x in list_open_close]
        optimize_result = pd.DataFrame({'open_close' : list_open_close})
        source2.data = {
            'reactor'    : [x for x in range(1,6)],
            'top'        : [1, 1, 1, 1, 1],
            'open_close' : optimize_result['open_close']
        }
        source3.data = {
            'reactor'   :['1'],
            'top':[list_open_close[-1]],
            'cap_target':[cap_target]
        }
        
# 수동 제어 인터페이스
html2 = """<h3>Manual Control Interface</h3>"""
div2 = Div(text=html2, style={'font-size': '150%'}, width=1000, height=60)
                           
# 일반 리액터와 가변 리액터 Tab 조정 
select_1 = Select(title="1st Reactor:", value="None", options=["Not Use", "Use"])
select_1.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))
select_2 = Select(title="2nd Reactor:", value="None", options=["Not Use", "Use"])
select_2.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))
select_3 = Select(title="3rd Reactor:", value="None", options=["Not Use", "Use"])
select_3.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))
select_4 = Select(title="4th Reactor:", value="None", options=["Not Use", "Use"])
select_4.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))
select_5 = Select(title="5th Reactor:", value="None", options=["Not Use", "Use"])
select_5.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))                         
select_6 = Select(title="Variable Reactor Tabs:", value="None", options=[str(x) for x in range(0,19)])
select_6.js_on_change("value", CustomJS(code="""
    console.log('select: value=' + this.value, this.toString())
"""))

controls = row(select_1, select_2, select_3, select_4, select_5, select_6)

# 전체 대시보드 layout 구성
curdoc().theme = 'contrast'
curdoc().title = "Dashboard"
curdoc().add_root(column(div, row(plot, toggle), row(plot2, plot3), div2, controls))
curdoc().add_periodic_callback(update, 3000) # ms 단위로 update 모듈 주기적으로 호출