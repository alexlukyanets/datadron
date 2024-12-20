from core.client.client import DataDroneClient

if __name__ == '__main__':
    client: DataDroneClient = DataDroneClient(
    )

    client.get_request()

