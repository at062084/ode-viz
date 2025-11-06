#!/usr/bin/env python3
"""
Create Superset Dashboard Programmatically

This script demonstrates how to create dashboards via Superset API.
Usage: python create_dashboard.py
"""

import requests
import json
from typing import Dict, Any


class SupersetAPI:
    def __init__(self, base_url: str = "http://localhost:8088"):
        self.base_url = base_url
        self.access_token = None
        self.headers = {"Content-Type": "application/json"}

    def login(self, username: str = "admin", password: str = "admin"):
        """Authenticate and get access token"""
        response = requests.post(
            f"{self.base_url}/api/v1/security/login",
            json={
                "username": username,
                "password": password,
                "provider": "db",
                "refresh": True
            }
        )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        print(f"✅ Logged in as {username}")

    def get_database_id(self, database_name: str = "examples") -> int:
        """Get database ID by name"""
        response = requests.get(
            f"{self.base_url}/api/v1/database/",
            headers=self.headers
        )
        response.raise_for_status()
        databases = response.json()["result"]

        for db in databases:
            if db["database_name"].lower() == database_name.lower():
                return db["id"]

        raise ValueError(f"Database '{database_name}' not found")

    def create_dataset(self, database_id: int, table_name: str) -> int:
        """Create a dataset from a table"""
        payload = {
            "database": database_id,
            "schema": "",
            "table_name": table_name
        }

        response = requests.post(
            f"{self.base_url}/api/v1/dataset/",
            json=payload,
            headers=self.headers
        )

        if response.status_code == 422:
            # Dataset might already exist
            print(f"⚠️  Dataset '{table_name}' might already exist")
            # Try to find it
            response = requests.get(
                f"{self.base_url}/api/v1/dataset/?q=(filters:!((col:table_name,opr:eq,value:'{table_name}')))",
                headers=self.headers
            )
            datasets = response.json()["result"]
            if datasets:
                print(f"✅ Found existing dataset: {table_name}")
                return datasets[0]["id"]
            raise Exception("Could not create or find dataset")

        response.raise_for_status()
        dataset_id = response.json()["id"]
        print(f"✅ Created dataset: {table_name} (ID: {dataset_id})")
        return dataset_id

    def create_chart(self, dataset_id: int, chart_config: Dict[str, Any]) -> int:
        """Create a chart"""
        payload = {
            "datasource_id": dataset_id,
            "datasource_type": "table",
            **chart_config
        }

        response = requests.post(
            f"{self.base_url}/api/v1/chart/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        chart_id = response.json()["id"]
        print(f"✅ Created chart: {chart_config['slice_name']} (ID: {chart_id})")
        return chart_id

    def create_dashboard(self, title: str, chart_ids: list) -> int:
        """Create a dashboard with charts"""
        payload = {
            "dashboard_title": title,
            "slug": title.lower().replace(" ", "-"),
            "published": True,
            "position_json": self._generate_position_json(chart_ids)
        }

        response = requests.post(
            f"{self.base_url}/api/v1/dashboard/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        dashboard_id = response.json()["id"]
        print(f"✅ Created dashboard: {title} (ID: {dashboard_id})")

        # Add charts to dashboard
        for chart_id in chart_ids:
            self._add_chart_to_dashboard(dashboard_id, chart_id)

        return dashboard_id

    def _generate_position_json(self, chart_ids: list) -> str:
        """Generate layout for dashboard charts"""
        # Simple 2-column layout
        position_data = {}
        row = 0
        col = 0

        for idx, chart_id in enumerate(chart_ids):
            position_data[f"CHART-{chart_id}"] = {
                "type": "CHART",
                "id": chart_id,
                "children": [],
                "meta": {
                    "width": 6,  # Half width
                    "height": 50,
                    "chartId": chart_id
                }
            }

            col += 6
            if col >= 12:
                col = 0
                row += 50

        return json.dumps(position_data)

    def _add_chart_to_dashboard(self, dashboard_id: int, chart_id: int):
        """Add a chart to a dashboard"""
        # This is handled by position_json in create_dashboard
        pass


def create_austrian_employment_dashboard():
    """
    Create a sample dashboard for Austrian employment data
    """

    # Initialize API
    api = SupersetAPI()
    api.login()

    # Get database
    database_id = api.get_database_id("examples")

    # Create dataset (assuming CSV was uploaded as 'austrian_employment')
    table_name = "austrian_employment"
    dataset_id = api.create_dataset(database_id, table_name)

    # Define charts
    charts = [
        {
            "slice_name": "Employment Over Time by Gender",
            "viz_type": "echarts_timeseries_line",
            "params": json.dumps({
                "time_column": "Datum",
                "metrics": ["SUM(BESTAND)"],
                "groupby": ["Geschlecht"],
                "time_grain_sqla": "P1M",  # Monthly
                "x_axis_time_format": "%Y-%m",
            })
        },
        {
            "slice_name": "Education Level Distribution",
            "viz_type": "pie",
            "params": json.dumps({
                "metrics": ["SUM(BESTAND)"],
                "groupby": ["HoeAbgAusbildung"],
                "row_limit": 10,
                "sort_by_metric": True,
            })
        },
        {
            "slice_name": "Regional Comparison",
            "viz_type": "echarts_timeseries_bar",
            "params": json.dumps({
                "metrics": ["SUM(BESTAND)", "SUM(ZUGANG)", "SUM(ABGANG)"],
                "groupby": ["RGSName"],
                "row_limit": 15,
            })
        },
        {
            "slice_name": "Total Employment",
            "viz_type": "big_number_total",
            "params": json.dumps({
                "metric": "SUM(BESTAND)",
                "time_column": "Datum",
            })
        }
    ]

    # Create charts
    chart_ids = []
    for chart_config in charts:
        try:
            chart_id = api.create_chart(dataset_id, chart_config)
            chart_ids.append(chart_id)
        except Exception as e:
            print(f"❌ Failed to create chart '{chart_config['slice_name']}': {e}")

    # Create dashboard
    dashboard_id = api.create_dashboard(
        "Austrian Employment Analysis",
        chart_ids
    )

    print(f"\n🎉 Dashboard created successfully!")
    print(f"📊 View it at: http://localhost:8088/superset/dashboard/{dashboard_id}/")


if __name__ == "__main__":
    print("🚀 Creating Austrian Employment Dashboard...\n")
    create_austrian_employment_dashboard()
