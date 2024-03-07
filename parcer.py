import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By

executor = ThreadPoolExecutor()


async def getDayScreenshot(url, numDay, element_id, save_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _getDayScreenshot, url, numDay, element_id, save_path)


async def getWeekScreenshot(url, numWeek, element_id, save_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _getWeekScreenshot, url, numWeek, element_id, save_path)


def _getDayScreenshot(url, numDay, element_id, save_path):
    driver = None

    try:
        optionsChrome = webdriver.ChromeOptions()
        optionsChrome.add_argument('--headless')
        driver = webdriver.Chrome(options=optionsChrome)
        driver.set_window_size(640, 1080)
        driver.get(url)

        elements = driver.find_elements(By.CLASS_NAME, element_id)
        innerDivs = elements[numDay].find_elements(By.CLASS_NAME, 'day-lesson')
        nonEmptyDivs = [div for div in innerDivs if div.text.strip() != ""]
        if nonEmptyDivs:
            driver.execute_script("arguments[0].scrollIntoView();", elements[numDay])
            elements[numDay].screenshot(save_path)
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if driver:
            driver.quit()



def _getWeekScreenshot(url, numWeek, element_id, save_path):
    optionsChrome = webdriver.ChromeOptions()
    optionsChrome.add_argument('--headless')
    optionsChrome.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(options=optionsChrome)
    driver.execute_script("document.body.style.zoom='65%'")
    driver.get(url)

    elements = driver.find_elements(By.CLASS_NAME, element_id)
    driver.execute_script("arguments[0].scrollIntoView();", elements[numWeek])
    elements[numWeek].screenshot(save_path)
    driver.quit()
