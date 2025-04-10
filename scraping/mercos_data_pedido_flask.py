import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import quote
import html
import sys

def get_driver():
    options = Options()
    
    user_profile_path = os.path.join(
    os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data"
    )

    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    
    options.add_argument("--log-level=3")  # 0 = ALL, 3 = ERROR only
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    options.add_argument(f"user-data-dir={user_profile_path}")
    options.add_argument("--profile-directory=Default")  
    
    try:
        return webdriver.Edge(options=options)
    except WebDriverException as e:
        print(f"Erro ao criar o driver: {e}. Tentando novamente em 5 segundos...")
        sleep(5)
        return get_driver()

def close_browser_process():
    os.system('taskkill /f /im msedge.exe >nul 2>&1')
    os.system("taskkill /f /im msedgedriver.exe >nul 2>&1")

def login(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "botaoEfetuarLogin"))).click()
    except TimeoutException:
        None
        
def search_order(driver, code):
    input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_texto")))
    input_element.clear()
    input_element.send_keys(code)
    input_element.send_keys(Keys.RETURN)
    
def open_order_details(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.CLASS_NAME,'link-pedido'))).click()
            # #fofex
            # '//*[@id="js-div-global"]/div[1]/section/div[2]/div[1]/div[4]/div[2]/div[1]/div[2]/span[3]'
            # #meu love
            # //*[@id="js-div-global"]/div[1]/section/div[4]/div[1]/div[4]/div[2]/div[1]
        
    except TimeoutException:
        print("Pedido não achado")
        return False
     
def extract_client_info(driver):
    return {
        "Fantasia": html.unescape(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="selecionado_autocomplete_id_codigo_cliente"]/span/div/div[1]/div[1]/h5/a'))).text),
        "Razao Social": html.unescape(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="selecionado_autocomplete_id_codigo_cliente"]/span/div/div[1]/div[1]/h5/small[1]'))).text.lstrip("- ")),
        "CNPJ": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="selecionado_autocomplete_id_codigo_cliente"]/span/div/div[1]/div[1]/h5/small[2]'))).text.lstrip("-"),
        "Cidade": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="selecionado_autocomplete_id_codigo_cliente"]/span/div/div[3]/div/span'))).text
    }

def expand_order_items(driver):
    try:
        show_all_itens = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "link_ver_mais")))
        driver.execute_script("arguments[0].click();", show_all_itens)
    except TimeoutException:
        pass
    
def extract_order_items(driver):
    request_itens = driver.find_elements(By.CLASS_NAME, "dados_item")
    request = []
    
    for request_item in request_itens:
        colums = request_item.find_elements(By.TAG_NAME, "td")
        
        if len(colums) > 10:
            item = {
                "Codigo": colums[1].text.strip(),
                "Descricao": colums[2].text.strip(),
                "Quantidade": colums[3].text.strip(),
                "Preco Tab.": colums[4].text.strip(),
                "Preco Liquido": colums[7].text.strip(),
                "IPI": colums[8].text.strip(),
                "Subtotal": colums[9].text.strip(),
            }
        else:
            item = {
                "Codigo": colums[1].text.strip(),
                "Descricao": colums[2].text.strip(),
                "Quantidade": colums[3].text.strip(),
                "Preco Tab.": colums[4].text.strip(),
                "Preco Liquido": colums[7].text.strip(),
                "IPI": '---',
                "Subtotal": colums[8].text.strip(),
            }
        request.append(item)
    
    return request

def extract_order_summary(driver):
    return {
        "Valor Pedido": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rodape_itens_pedido_js"]/div[1]/div[6]/div/strong'))).text,
        "Data Pedido": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="informacoes_complementares"]/div/div/div[1]/div[2]/div/div[2]'))).text,
        "Tipo Pedido": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="informacoes_complementares"]/div/div/div[1]/div[3]/div/div[2]'))).text,
        "Vendedor": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="informacoes_complementares"]/div/div/div[1]/div[4]/div/div[2]'))).text,
        "Condicao Pagamento": WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="informacoes_complementares"]/div/div/div[2]/div/div/div[2]'))).text
    }

def save_csv(dados, file_path, write_header):
    if not dados:
        return

    df = pd.json_normalize(dados, record_path="Pedido", meta=[col for col in dados[0] if col != "Pedido"])
    df.to_csv((file_path + ".csv"), mode='a', index=False, header=write_header)

def format_url_by_date(enterprise, initial_date: str, final_date: str) -> str:
    base_url = 'https://app.mercos.com/{}/pedidos/?tipo_pesquisa=1&texto=&tipo_de_pedido=&cliente=&nota_fiscal=&data_emissao_inicio={}&data_emissao_fim={}&status=2&criador=&equipe=&plataforma=&enviado_representada=&status_custom='

    # Garante o encode correto (05%2F04%2F2025)
    encoded_initial = quote(initial_date, safe='')
    encoded_final = quote(final_date, safe='')

    return base_url.format(enterprise, encoded_initial, encoded_final)

def click_next_page(driver):
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Próxima »")]'))).click()
        sleep(2) 
        return True
    except Exception:
        return False

def extract_order_codes(driver, url):
    login(driver, url)
    driver.get(url)
    
    all_codes = []
    try:
        while True:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "numero-pedido")))

            elements = driver.find_elements(By.CLASS_NAME, "numero-pedido")
            for el in elements:
                code = el.text.lstrip("#").strip()
                all_codes.append(code)
                
            if not click_next_page(driver):
                break
        return all_codes
    
    except TimeoutException:
        print("Não foram encontrados pedidos dentro do intervalo das datas")
        return []
        
def process_lote(driver, lote, url):
    lote_dados = []
    login(driver, url)
    
    for code in lote:
        try:
            search_order(driver, str(code))
            try:
                open_order_details(driver)
            except:
                print(f"Pedido {code} não foi concluído.")
                continue

            client_info = extract_client_info(driver)
            expand_order_items(driver)
            order_items = extract_order_items(driver)
            order_summary = extract_order_summary(driver)

            client_info.update(order_summary)
            client_info["Codigo do Pedido"] = code
            client_info["Pedido"] = order_items

            lote_dados.append(client_info)

        except TimeoutException:
            print(f"Timeout no código {code}. Pulando.")
        except Exception as e:
            print(f"Erro no código {code}: {e}")
            
        driver.back()
    return lote_dados

def main(enterprise, initial_date, final_date, progress_callback=None):
    url_all_orders = f"https://app.mercos.com/{enterprise}/pedidos/"
    url_filtered  = format_url_by_date(enterprise, initial_date, final_date)
    
    lote_size = 5

    close_browser_process()
    driver = get_driver()
    order_codes = extract_order_codes(driver, url_filtered)
    driver.quit()
    
    total = len(order_codes)
    progress = 0
    
    if total == 0:
        if progress_callback:
            progress_callback(100, total)
        return []

    all_data = []
    for i in range(0, total, lote_size):
        lote = order_codes[i:i + lote_size]

        driver = get_driver()
        lote_dados = process_lote(driver, lote, url_all_orders)
        
        driver.delete_all_cookies()
        driver.quit()
        
        all_data.extend(lote_dados)

        progress += len(lote)  
        percent = int((progress / total) * 100)
        
        if progress_callback:
            progress_callback(percent, total)
    return all_data

# if __name__ == "__main__":
#     main()
    
    
    
    
    
    
    
    
    
    

# //*[@id="form_pesquisa_normal"]/div[2]/a/small #link para expandir o filtro

# //*[@id="id_data_emissao_inicio"] #imput da data

# //*[@id="id_data_emissao_fim"] #imput da data

# //*[@id="pesquisa_avancada"]/div/div[2]/button #botão pesquisar por filtro

# //*[@id="js-div-global"]/div[1]/section/div[2]/div[1]/div[4]/div[23]/a #botão proxima pagina
# //*[@id="js-div-global"]/div[1]/section/div[2]/div[1]/div[4]/div[24]/a[2] #botão proxima pagina quando aparece 'anterior'

# #url para pedidos por data, 'status=2' so pega os concluidos
# https://app.mercos.com/393186/pedidos/?tipo_pesquisa=1&texto=&tipo_de_pedido=&cliente=&nota_fiscal=&data_emissao_inicio=05%2F04%2F2025&data_emissao_fim=07%2F04%2F2025&status=2&criador=&equipe=&plataforma=&enviado_representada=&status_custom=

# WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "small-box")))

# WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "numero-pedido")))
# driver.find_elements(By.CLASS_NAME, "numero-pedido")