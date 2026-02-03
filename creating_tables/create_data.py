import boto3

def create_table_1():
    # Yine İrlanda bölgesine bağlanıyoruz ki verilerle tablo aynı yerde olsun
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

    print("⏳ 'pharma_products' tablosu oluşturuluyor...")

    try:
        table = dynamodb.create_table(
            TableName='pharma_products',
            KeySchema=[
                {
                    'AttributeName': 'drug_id',
                    'KeyType': 'HASH'  # Partition Key (Birincil Anahtar)
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'drug_id',
                    'AttributeType': 'S' # String (Metin)
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        

        print("⏳ AWS tabloyu hazırlıyor, lütfen bekleyin...")
        table.wait_until_exists()
        print("✅ BAŞARILI: Tablo kullanıma hazır!")
        
    except Exception as e:
        print("⚠️ Bir durum oluştu (Belki tablo zaten vardır):")
        print(e)


TABLE_NAME = 'sales_transactions'
def create_table_2():
    # 1. AWS DynamoDB servisine bağlanıyoruz (Boto3 Resource)
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    
    # 2. Mevcut tabloların listesini alıyoruz (Hata almamak için kontrol)
    existing_tables = [t.name for t in dynamodb.tables.all()]
    
    # 3. Eğer tablomuz listede YOKSA, oluşturmaya başla
    if TABLE_NAME not in existing_tables:
        print(f"🔨 Tablo inşa ediliyor: {TABLE_NAME}...")
        
        # 4. Tablo Oluşturma Komutu (Create Table)
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            # KeySchema: Tablonun Anahtarları (Kimlik Kartı)
            KeySchema=[
                {'AttributeName': 'transaction_id', 'KeyType': 'HASH'},  # Partition Key (Benzersiz ID)
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}       # Sort Key (Zamana göre sırala)
            ],
            # AttributeDefinitions: Anahtarların Tipi (String, Number...)
            AttributeDefinitions=[
                {'AttributeName': 'transaction_id', 'AttributeType': 'S'}, # S = String (Metin)
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}       # S = String (Tarih metni)
            ],
            # ProvisionedThroughput: Kapasite Ayarı (Hız limiti)
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # 5. Tablo oluşana kadar bekle (AWS'de işlem 10-20 sn sürebilir)
        table.wait_until_exists()
        print("✅ Tablo başarıyla oluşturuldu ve kullanıma hazır!")
    else:
        print(f"ℹ️  Bilgi: {TABLE_NAME} tablosu zaten var, tekrar oluşturulmadı.")



if __name__ == "__main__":
    create_table_1()
    create_table_2()