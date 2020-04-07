import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import os
import base64
import img2pdf
from PIL import Image

album_cover_url = 'https://web.vip.miui.com/page/info/mi-fans'
album_url = album_cover_url + '/album'

save_path = 'img'


# 获取相册封面
def get_album_cover():
    driver.get(album_cover_url)
    album_cover_img = []
    try:
        album_cover_img.append(driver.find_element_by_xpath('//div[@class="home-bg"]/img').get_attribute('src'))
    except Exception as e:
        print('获取相册封面失败：{}'.format(e))

    print(album_cover_img)
    return album_cover_img


# 获取相册图片
def get_album():
    driver.get(album_url)
    album_img = []
    try:
        album_node = driver.find_elements_by_xpath('//div/img')
        for node in album_node:
            album_img.append(node.get_attribute('src'))
    except Exception as e:
        print('获取相册内容失败：{}'.format(e))

    print(album_img)
    return album_img


def download_album(albums, album_type):
    for index, album in enumerate(albums):
        index += 1
        if index <= 9:
            index = '0{}'.format(index)

        path = os.path.join(save_path, '{}{}.jpg'.format(album_type, index))
        if os.path.exists(path):
            print('{}{}.jpg ==> 已经下载'.format(album_type, index))
            continue

        if 'data:image/png' in album:
            # 图片解码
            album = decode_image(album)
        else:
            album = requests.get(album).content

        with open(path, 'wb') as file:
            file.write(album)
            print('{}{}.jpg ==> 下载成功'.format(album_type, index))


# data:image/png解码
def decode_image(album):
    result = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", album, re.DOTALL)
    if result:
        # ext = result.groupdict().get("ext")
        data = result.groupdict().get("data")
    else:
        raise Exception("图片地址解码失败")

    album = base64.urlsafe_b64decode(data)
    return album


# 将相册转换成PDF
def album2pdf():
    albums = os.listdir(save_path)
    album_cover = albums.pop()
    albums.insert(0, album_cover)
    albums = [os.path.join(save_path, album) for album in albums]

    remove_transparent(albums)

    a4inpt = (img2pdf.mm_to_pt(720), img2pdf.mm_to_pt(1080))
    layout_fun = img2pdf.get_layout_fun(a4inpt)
    with open('mi10years.pdf', 'wb') as f:
        f.write(img2pdf.convert(albums, layout_fun=layout_fun))


# 去除透明度，否则img2pdf不支持含有透明的图片写入
def remove_transparent(albums):
    for album in albums:
        img = Image.open(album)

        if img.mode == 'P':
            alpha = img.convert('RGBA').split()[-1]
            bg = Image.new('RGBA', img.size, 'white')
            bg.paste(img, mask=alpha)
            bg.convert('RGB').save(album)
        else:
            print('{} ==> 无需转换'.format(album))


if __name__ == '__main__':
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    if len(os.listdir(save_path)) == 67:
        print('相册封面和内容都已下载，无需重复下载')
    else:
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        download_album(get_album_cover(), 'cover')
        download_album(get_album(), 'content')

        driver.quit()

    album2pdf()
