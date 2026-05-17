from django.shortcuts import render
import pygetwindow as gw

# Create your views here.
def window_selector(request):

    page_title = "視窗選擇"
    # 取得所有視窗標題的串列
    all_titles = gw.getAllTitles()
    for title in all_titles:
        if title.strip():  # 過濾掉空白的視窗名稱
            print(title)
    windows = all_titles
    return render(request, 'window_selector.html', {'page_title': page_title, 'windows': windows})