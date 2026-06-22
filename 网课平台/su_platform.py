"""
此代码仅用于粟湾科技平台（或许其他相似的平台也能用）
个人练习用代码
"""

import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import logging
from selenium.common import NoSuchElementException
from io import BytesIO
from PIL import Image
import ddddocr
import random

# 日志设置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')


# 登录页面
URL = 'https://bwgl.suwankj.com/user/login' # 这里可更换为你需要的网址

# 账号密码 在此处修改你的账号和密码
USERNAME = ""
PASSWORD = ""

# 创建Edge浏览器实例
edge_options = webdriver.EdgeOptions()
edge_options.add_experimental_option("detach", True)
# 隐藏自动化特征，防止被识别为 Selenium
edge_options.add_argument("--disable-blink-features=AutomationControlled")
edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
browser = webdriver.Edge(options=edge_options)

# 执行脚本隐藏 webdriver 属性
browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """
})

wait = WebDriverWait(browser, 5)

def human_sleep(min_sec=2, max_sec=5):
    """模拟人类思考或网络波动的随机延迟"""
    time.sleep(random.uniform(min_sec, max_sec))


def random_mouse_move(browser, target_element=None):
    """
    模拟人类鼠标移动
    :param browser: 浏览器驱动
    :param target_element: (可选) 目标元素，如果提供则移动到该元素中心
    """
    action = ActionChains(browser)

    if target_element:
        # 如果有目标元素，移动到元素附近（带一点随机偏移）
        x_offset = random.randint(-10, 10)
        y_offset = random.randint(-10, 10)
        action.move_to_element_with_offset(target_element, x_offset, y_offset)
    else:
        # 如果没有目标，就在当前视口内随机移动一下
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        action.move_by_offset(x, y)

    # 执行移动
    action.perform()
    # 移动后也要随机停顿一下
    time.sleep(random.uniform(0.5, 1.5))

def login_su(url):
    """登录函数,用于登录网课平台
    :param url: 登录页面URL
    """
    logging.info('logining %s', url)
    # 打开网页
    browser.get(url)
    random_mouse_move(browser)

    # 确保窗口最大化
    browser.maximize_window()
    ActionChains(browser).move_to_element(browser.find_element(By.TAG_NAME, "body")).perform()  # 重置鼠标

    # 持续尝试登录直到成功
    while True:
        # 等待元素加载
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#username")))

        human_sleep(1,3)
        # 查找账号和密码输入框
        account = browser.find_element(By.CSS_SELECTOR, "#username")
        password = browser.find_element(By.CSS_SELECTOR, "#password")

        # 清空输入框（防止之前输入的内容残留）
        account.clear()
        password.clear()

        # 模拟逐个字符输入
        for char in USERNAME:
            account.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

        for char in PASSWORD:
            password.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

        # 获取登录按钮
        login_button = browser.find_element(By.CSS_SELECTOR, ".btn")

        # 获取并识别验证码
        captcha_image = get_captcha_image()
        if captcha_image:
            captcha_code = captcha(captcha_image)
            # 输入验证码（如果有验证码输入框）
            try:
                captcha_input = browser.find_element(By.CSS_SELECTOR, "#code")  # 根据实际ID修改
                captcha_input.clear()  # 清空验证码输入框
                human_sleep(1, 2)
                captcha_input.send_keys(captcha_code)

                human_sleep(1, 2)
                login_button.click()

                # 等待登录结果，判断是否成功
                time.sleep(random.uniform(2,4))

                # 检查是否还在登录页面（说明登录失败）
                try:
                    browser.find_element(By.CSS_SELECTOR, "#username")
                    logging.warning('登录失败，验证码可能错误，重新尝试中...')
                    # 刷新页面获取新验证码
                    human_sleep(2, 4)
                    browser.refresh()
                    human_sleep(2, 4)
                    continue  # 继续循环尝试
                except NoSuchElementException:
                    logging.info('验证码匹配成功！')
                    logging.info('登录成功！')
                    # 关闭可能出现的弹窗
                    time.sleep(1)  # 等待弹窗加载
                    close_buttons = browser.find_elements(By.CSS_SELECTOR, ".layui-layer-ico.layui-layer-close.layui-layer-close1")
                    if close_buttons:
                        close_buttons[0].click()

                    break  # 退出循环

            except NoSuchElementException:
                logging.warning('未找到验证码输入框')
                break  # 没有验证码输入框，可能是其他情况
        else:
            logging.error('获取验证码失败，重新尝试...')
            browser.refresh()
            time.sleep(1)
            continue

def get_captcha_image():
    """获取验证码图片并返回 PIL Image 对象"""
    try:
        # 等待
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.ID, "codeImg"))
        )

        # 额外等待确保图片完全加载
        time.sleep(1)

        # 定位验证码元素
        captcha_element = browser.find_element(By.CSS_SELECTOR, "#codeImg")

        # 验证元素尺寸
        if captcha_element.size['width'] == 0 or captcha_element.size['height'] == 0:
            logging.error('验证码元素尺寸为0，可能被遮挡或未加载')
            return None

        human_sleep(1,2)
        # 截图到内存（不保存文件）
        img_bytes = captcha_element.screenshot_as_png
        image = Image.open(BytesIO(img_bytes))

        logging.info('尝试获取验证码图片...')
        return image

    except TimeoutException:
        logging.error('等待验证码元素超时')
        return None
    except NoSuchElementException:
        logging.error('验证码元素未找到')
        return None


def captcha(img):
    """
    :param img: 验证码图片
    :return:返回验证码字符串
    """

    # 验证码识别器
    ocr = ddddocr.DdddOcr(show_ad=False)

    time.sleep(3)

    # 图片转字节
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # 重试3次，防止空值
    result = ""
    for _ in range(3):
        result = ocr.classification(img_bytes).strip()
        if result:
            break

    logging.info('识别结果：%s', result)
    return result

def get_courses_list():
    """获取课程列表
    :return dict {课程名称: 课程URL}
    """
    try:
        a_div = browser.find_element(By.CSS_SELECTOR, ".user-course")
        link_elements = a_div.find_elements(By.CSS_SELECTOR, ".name a")
        courses_dict = {link.text: link.get_attribute('href') for link in link_elements if link.text and link.get_attribute('href')}
        logging.info(f'获取课程列表成功! 共 {len(courses_dict)} 门课程')
        return courses_dict

    except NoSuchElementException:
        logging.error('未找到课程列表')
        return {}

def judge_captcha():
    """判断是否需要处理点击播放后弹出的验证码
    :return: bool - True表示有可见的验证码弹窗，False表示无弹窗或弹窗已隐藏
    """
    try:
        # 查找所有 layui-layer 弹窗元素（不等待，立即返回）
        WebDriverWait(browser, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".layui-layer"))
        )
        return True

    except Exception as e:
        logging.debug('没有验证码弹窗')
        return False

def handle_play_captcha():
    """处理点击播放后弹出的验证码"""
    try:
        # 等待弹窗完全加载
        time.sleep(3)

        img = get_captcha_image()
        if not img:
            logging.error('获取验证码图片失败')
            return

        captcha_code = captcha(img)

        # 查找输入框（尝试多种选择器）
        captcha_input = None
        input_selectors = [
            (By.CSS_SELECTOR, '[placeholder*="验证码"]'),
            (By.XPATH, '//input[contains(@placeholder, "验证码")]'),
            (By.CSS_SELECTOR, '.layui-layer-content input[type="text"]'),
        ]

        for by, selector in input_selectors:
            try:
                elements = browser.find_elements(by, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                if visible_elements:
                    captcha_input = visible_elements[0]
                    logging.info(f'找到输入框: {selector}')
                    break
            except:
                continue

        if not captcha_input:
            logging.error('未找到验证码输入框')
            return

        # 查找确认按钮
        play_btn = None
        btn_selectors = [
            (By.CSS_SELECTOR, '.layui-layer-btn0'),
            (By.XPATH, '//button[contains(text(), "确定") or contains(text(), "提交")]'),
        ]

        for by, selector in btn_selectors:
            try:
                elements = browser.find_elements(by, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                if visible_elements:
                    play_btn = visible_elements[0]
                    logging.info(f'找到按钮: {selector}')
                    break
            except:
                continue

        if not play_btn:
            logging.error('未找到确认按钮')
            return

        # 使用 JavaScript 设置输入框值（绕过交互限制）
        browser.execute_script("arguments[0].value = '';", captcha_input)
        browser.execute_script(f"arguments[0].value = '{captcha_code}';", captcha_input)
        logging.info('已通过JS输入验证码')

        # 短暂等待后点击按钮
        human_sleep(1,2)

        # 使用 JS 点击
        browser.execute_script("arguments[0].click();", play_btn)
        logging.info('验证码提交成功')
        time.sleep(1)

    except Exception as e:
        logging.error(f'处理验证码出错: {e}')
        import traceback
        logging.debug(traceback.format_exc())

def parse_video_duration(duration_text):
    """解析视频时长文本，返回秒数
    Args:
        duration_text: 格式为 "00:00 / 05:33" 的字符串

    Returns:
        总时长（秒），解析失败返回 None
    """
    try:
        # 提取总时长部分（斜杠后面）
        total_time_str = duration_text.split('/')[1].strip()
        parts = total_time_str.split(':')

        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds + 2
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds + 2
        else:
            logging.warning(f'无法解析时长格式: {duration_text}')
            return None
    except (IndexError, ValueError) as e:
        logging.error(f'解析时长出错: {e}')
        return None

def view_course(url, course_begin_index=1):

    browser.get(url)
    # 等待课程名称加载，确保页面加载完整
    human_sleep(2, 5)

    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".ncoursecon-intro .name")))
    except TimeoutException:
        logging.error('课程页面加载超时')
        return

    # 获取课程名称
    name_div = browser.find_element(By.CSS_SELECTOR, ".ncoursecon-intro .name")
    course_name = name_div.text

    # 尝试进入课程详情页面
    try:
        inter_btn = browser.find_elements(By.CSS_SELECTOR, ".btn1")
        if len(inter_btn) < 2:
            logging.error('未找到观看按钮')
            return

        view_btn = inter_btn[1]
        view_btn.click()
        logging.info(f'准备观看课程：{course_name}')

        # 等待章节列表加载
        time.sleep(2)

        # 获取章节数量
        chapters_count = len(browser.find_elements(By.CSS_SELECTOR, '.detmain-navlist .group.two'))
        logging.info(f'共找到 {chapters_count} 个章节')

        # 收集所有章节和课程信息
        all_courses = []
        scroll_height = random.randint(200, 500)
        browser.execute_script(f"window.scrollBy(0, {scroll_height});")
        human_sleep(1, 2)

        for i in range(chapters_count):
            try:
                # 每次循环重新查找章节元素，避免StaleElementReferenceException
                chapters = browser.find_elements(By.CSS_SELECTOR, '.detmain-navlist .group.two')
                # 由于每次循环都重新查找chapters元素，页面动态变化可能导致章节数量减少，
                # 此检查确保不会访问不存在的元素索引，避免IndexError异常。
                if i >= len(chapters):
                    break

                # 获取章节标题
                chapter = chapters[i]
                title = chapter.find_element(By.CSS_SELECTOR, 'a').get_attribute('title')
                logging.info(f'正在处理章节：{title}')

                # 尝试进入单章节
                try:
                    # 展开章节
                    btn = chapter.find_element(By.CSS_SELECTOR, '.name a')
                    human_sleep(2,4)
                    browser.execute_script("arguments[0].click();", btn)

                    # 等待展开动画完成和.item元素加载
                    human_sleep(2,4)

                    # 查找.list容器
                    chapter_courses_parent = chapter.find_element(By.CSS_SELECTOR, '.list')
                    human_sleep(2,5)

                    # 显式等待.item元素出现
                    try:
                        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list .item')))
                    except TimeoutException:
                        logging.warning(f'章节 {title} 未找到课程项(.item)')
                        continue

                    human_sleep(2,5)
                    # 获取章节课程
                    chapter_courses = chapter_courses_parent.find_elements(By.CSS_SELECTOR, '.item')
                    logging.info(f'章节 {title} 包含 {len(chapter_courses)} 个课程')

                    # 提取课程信息
                    # 此举动防止页面动态变化导致元素丢失，而抛出StaleElementReferenceException异常。
                    for course_item in chapter_courses:
                        try:
                            course_title = course_item.find_element(By.CSS_SELECTOR, 'a').get_attribute('title')
                            course_url = course_item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                            # 将提取到的课程信息添加到列表中
                            if course_title and course_url:
                                all_courses.append((title, course_title, course_url))
                        except NoSuchElementException:
                            continue

                except NoSuchElementException:
                    logging.warning(f'章节 {title} 结构异常，跳过')
                    continue

            except Exception as e:
                logging.error(f'处理章节 {i + 1} 时出错: {e}')
                continue

        # 播放所有课程
        num = 1
        logging.info(f'{'-'*8}共收集到 {len(all_courses)} 个课程，开始播放...{'-'*8}')
        for chapter_title, course_title, course_url in all_courses[course_begin_index-1:]:
            try:
                browser.get(course_url)
                human_sleep(3, 6) # 进入视频页多等一会儿

                # 尝试获取该视频总时长（注：时间节点的class属性会发生变化）
                try:
                    all_time_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "/") and contains(@style, "float: left")]')))
                    all_time = all_time_element.text
                    time_seconds = parse_video_duration(all_time)
                except TimeoutException:
                    logging.error('未找到总时长元素')
                    continue

                # 开始播放(同上，网站具备反爬机制，class在不断改变，无法精确定位)
                try:
                    logging.info(f'准备播放课程第 {num+course_begin_index-1}个课程，总时长为 {all_time}')
                    play_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-title="点击播放"]')))
                    random_mouse_move(browser, play_btn)  # 先移到按钮附近
                    human_sleep(1, 2)  # 犹豫一下
                    play_btn.click()

                    human_sleep(2,5)
                    # 检测是否有验证码弹窗，最多重试5次
                    max_captcha_retry = 5
                    for attempt in range(max_captcha_retry):
                        if not judge_captcha():
                            logging.info('无需验证码或验证已通过')
                            break

                        logging.info(f'检测到验证码弹窗，第 {attempt + 1} 次尝试...')
                        human_sleep(3,6)
                        handle_play_captcha()

                        # 等待验证结果
                        time.sleep(5)

                        browser.get(course_url)
                        play_btn = wait.until(
                            EC.presence_of_element_located((By.XPATH, '//div[@data-title="点击播放"]')))
                        # 尝试点击播放按钮,试图刷新验证码
                        human_sleep(2,5 )
                        play_btn.click()

                        # 再次检查是否还有可见的验证码弹窗
                        if not judge_captcha():
                            logging.info('验证码验证通过')
                            break
                        else:
                            logging.warning(f'验证码可能错误，剩余重试次数: {max_captcha_retry - attempt - 1}')
                    else:
                        logging.error(f'验证码处理失败，已重试 {max_captcha_retry} 次，跳过当前视频')
                        continue

                    logging.info(f'正在播放 [{chapter_title}] - {course_title}')
                    time.sleep(time_seconds + random.uniform(5,11))
                    logging.info(f'播放完毕，尝试播放下一个视频......')
                    num+=1
                except TimeoutException:
                    logging.error('未找到播放按钮')
                    continue

            except Exception as e:
                logging.error(f'播放课程 {course_title} 时出错: {e}')
                continue
    except IndexError:
        logging.error('按钮索引超出范围')
    except Exception as e:
        logging.error(f'view_course执行出错: {e}')

def view_all_courses(chapter_begin_index=1,course_begin_index=1):
    """
    遍历并观看该网课平台的所有课程
    :param chapter_begin_index: 指定起始课程的索引（从1开始），默认为1
    :param course_begin_index: 指定课程内起始视频的索引（从1开始），默认为1
    """
    for course_url in list(get_courses_list().values())[chapter_begin_index-1:]:
        view_course(course_url, course_begin_index)
        logging.info(f'{'-'*8}课程 {course_url} 播放完毕{'-'*8}')
        course_begin_index = 1
    logging.info('所有课程播放完毕')

def view_single_course(input_course_name, course_begin_index=1):
    """
    :param input_course_name: 指定的课程名称 eg：心理文化学基础
    :param course_begin_index: 指定的课程起始索性，不传入参数默认从第1个视频开始，eg：传入12，则从第12个视频开始
                                注意区分章节与章节内视频，视频索引是连续的，不因章节发生变化导致视频索引变为1
    :return: none
    """
    for course_name, course_url in get_courses_list().items():
        if course_name == input_course_name:
            view_course(course_url, course_begin_index)
            logging.info(f'课程 {course_name} 播放完毕')
            return
    logging.error(f'未找到课程 {input_course_name}')

def main():
    login_su(URL)
    # 调用函数，进行自动看网课，以下为示例
    view_all_courses(2,13)
    # view_all_courses(2,9)  # 播放，从第2个课程，第9个视频开始
    # view_single_course('心理文化学基础', 12) # 只播放第2个课程且从第12个视频开始

if __name__ == '__main__':
    main()

