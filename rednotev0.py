from selenium import webdriver

# 启动 Chrome 浏览器
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 无头模式
driver = webdriver.Chrome(options=options)

# 访问小红书
driver.get("https://www.xiaohongshu.com")

# 获取 Cookies
cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
user_agent = driver.execute_script("return navigator.userAgent;")

print("Cookies:", cookies)
print("User-Agent:", user_agent)

driver.quit()
