from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import os

from playwright._impl._errors import TimeoutError

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output/receipts", exist_ok=True)

    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
    
    archive_receipts()

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/")
    browser.page().click("text=Order your robot!")

def get_orders():
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    
    orders = Tables().read_table_from_csv(path="orders.csv", header=True).to_list()

    return orders

def close_annoying_modal():
    page = browser.page()
    page.click("text=OK")

def fill_the_form(order):
    page = browser.page()

    page.click("text=Show model info")

    page.select_option("#head", order["Head"])

    body_element_selector = f"#id-body-{order['Body']}"
    page.click(body_element_selector)

    page.fill("//*[@class='form-control' and @type='number']", order["Legs"])

    page.fill("#address", order["Address"])

    page.click("#preview")

    order_submitted_successfuly = False
    while not order_submitted_successfuly:
        page.click("#order")

        try:
            pdf_file_path = store_receipt_as_pdf(order["Order number"])
        except TimeoutError:
            pass
        else:
            screenshot_path = screenshot_robot(order["Order number"])
            page.click("#order-another", timeout=2000)
            embed_screenshot_to_receipt(screenshot_path, pdf_file_path)
            order_submitted_successfuly = True

def store_receipt_as_pdf(order_number):
    page = browser.page()
    
    page.wait_for_selector("#receipt", timeout=2000)
    receipt_html = page.locator("#receipt").inner_html()
    
    pdf = PDF()
    pdf_file_path = f"output/receipts/{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, pdf_file_path)

    return pdf_file_path

def screenshot_robot(order_number):  
    page = browser.page()
    robot_image_locator = page.locator("#robot-preview-image")
    
    robot_image_bytes = browser.screenshot(robot_image_locator)

    robot_image_file_path = f"output/images/{order_number}.png"

    with open(robot_image_file_path, "wb") as image_file:
        image_file.write(robot_image_bytes)

    return robot_image_file_path

def embed_screenshot_to_receipt(screenshot_path, pdf_file_path):
    pdf = PDF()

    pdf.add_watermark_image_to_pdf(
        image_path=screenshot_path, 
        source_path=pdf_file_path, 
        output_path=pdf_file_path, 
    )

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('output/receipts', 'output/receipts.zip')
