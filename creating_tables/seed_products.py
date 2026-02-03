import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('pharma_products') 

def seed_data():
    print("🌱 Ürün verisi ekleniyor...")
    table.put_item(
        Item={
            'drug_id': 'OTC_VIT_C_ZINC', 
            'product_name': 'Vitamin C + Zinc Complex',
            'stock_level': Decimal(2000),  
            'current_price': Decimal(120), 
            'competitor_price': Decimal(130), 
            'cost_price': Decimal(60), 
            'category': 'Supplements'
        }
    )
    print("✅ Ürün başarıyla eklendi/sıfırlandı!")

if __name__ == "__main__":
    seed_data()