from core.client.client import DataDroneClient

if __name__ == '__main__':
    client: DataDroneClient = DataDroneClient(
        timeout=10,
        verify=False,
        follow_redirects=True
    )

    client.get(
        url='https://example.com',
        timeout=10
    )

