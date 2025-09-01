import re

from requests import get
from selenium.webdriver.common.by import By


def get_classes(element):
    classes = set()
    for style in element.get_attribute('class').split(' '):
        classes.add(style)
    for child in element.find_elements(By.CSS_SELECTOR, '*'):
        for style in get_classes(child):
            classes.add(style)
    return classes


def get_css(driver):
    combined_styles = ''
    styles = driver.find_elements(By.XPATH, '//link[@rel="stylesheet"]')
    for style in styles:
        text = style.get_attribute('outerHTML')
        combined_styles += text + '\n'
    return combined_styles


def parse_css(css, classes=None):
    css = re.sub(r'\s+', ' ', css)
    styles = css.split('}')
    style_dict = dict()
    for style in styles:
        if len(style) > 0:
            split = style.split('{')
            key = split[0].strip()
            style_dict[key] = '{ ' + split[1] + ' }'
    if classes:
        return {key: value for key, value in style_dict.items() if key in classes}
    return style_dict


def get_value(driver, xpath):
    split = xpath.split('/')
    attribute = ''
    path = xpath
    if split[-1].startswith('@'):
        path = '/'.join(split[0:-1])
        attribute = split[-1].replace('@', '')
    element = driver.find_element(By.XPATH, path)
    if attribute:
        return element.get_attribute(attribute)
    else:
        return element.get_attribute('outerHTML')
