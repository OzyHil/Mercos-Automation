def baixar_csv():
#     global dados_global, file_path_global

#     if not dados_global:
#         return "Nenhum dado para baixar", 400
    
#     # Verifica se o arquivo já existe para decidir se inclui cabeçalho
#     write_header = not os.path.exists(file_path_global + ".csv")

#     # Salva os dados no CSV
#     save_csv(dados_global, f'data/{file_path_global}', write_header, tipo_extracao)

#     # Envia o arquivo como download
#     return send_file(f"data/{file_path_global}.csv", as_attachment=True)