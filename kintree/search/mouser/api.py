import json

from .base import MouserBaseRequest


class MouserCartRequest(MouserBaseRequest):
    """ Mouser Cart Request """

    name = 'Cart'
    operations = {
        'get': ('', ''),
        'update': ('', ''),
        'insertitem': ('', ''),
        'updateitem': ('', ''),
        'removeitem': ('', ''),
    }


class MouserOrderHistoryRequest(MouserBaseRequest):
    """ Mouser Order History Request """

    name = 'Order History'
    operations = {
        'ByDateFilter': ('', ''),
        'ByDateRange': ('', ''),
    }


class MouserOrderRequest(MouserBaseRequest):
    """ Mouser Order Request """

    name = 'Order'
    operations = {
        'get': ('GET', '/order'),
        'create': ('', ''),
        'submit': ('', ''),
        'options': ('', ''),
        'currencies': ('', ''),
        'countries': ('', ''),
    }

    def export_order_lines_to_csv(self, order_number='', clean=False):
        ''' Export Order Lines to CSV '''

        def convert_order_lines_to_list(clean=False):

            if clean:
                # Exclude following columns
                exclude_col = [
                    'Errors',
                    'MouserATS',
                    'PartsPerReel',
                    'ScheduledReleases',
                    'InfoMessages',
                    'CartItemCustPartNumber',
                    'LifeCycle',
                    'SalesMultipleQty',
                    'SalesMinimumOrderQty',
                    'SalesMaximumOrderQty',
                ]
            else:
                exclude_col = []

            response_data = self.get_response()
            data_list = []
            if 'OrderLines' in response_data:
                order_lines = response_data['OrderLines']

                headers = [key for key in order_lines[0] if key not in exclude_col]
                data_list.append(headers)

                for order_line in order_lines:
                    line = [value for key, value in order_line.items() if key not in exclude_col]
                    data_list.append(line)

                return data_list

        data_to_export = convert_order_lines_to_list(clean)
        filename = '_'.join([self.name, order_number]) + '.csv'
        # Export to CSV file
        self.export_csv(filename, data_to_export)

        return filename


class MouserPartSearchRequest(MouserBaseRequest):
    """ Mouser Part Search Request """

    name = 'Part Search'
    operations = {
        'keyword': ('', ''),
        'keywordandmanufacturer': ('', ''),
        'partnumber': ('POST', '/search/partnumber'),
        'partnumberandmanufacturer': ('', ''),
        'manufacturerlist': ('', ''),
    }

    def get_clean_response(self):
        cleaned_data = {
            'Availability': '',
            'Category': '',
            'DataSheetUrl': '',
            'Description': '',
            'ImagePath': '',
            'Manufacturer': '',
            'ManufacturerPartNumber': '',
            'MouserPartNumber': '',
            'ProductDetailUrl': '',
            'ProductAttributes': [],
            'PriceBreaks': [],
        }

        response = self.get_response()
        if self.get_response():
            try:
                parts = response['SearchResults'].get('Parts', [])
            except AttributeError:
                parts = None

            if parts:
                # Process first part
                part_data = parts[0]
                # Merge
                for key in cleaned_data:
                    cleaned_data[key] = part_data[key]

        return cleaned_data

    def print_clean_response(self):
        response_data = self.get_clean_response()
        print(json.dumps(response_data, indent=4, sort_keys=True))

    def get_body(self, **kwargs):

        body = {}

        if self.operation == 'partnumber':
            part_number = kwargs.get('part_number', None)
            option = kwargs.get('option', 'None')

            if part_number:
                body = {
                    'SearchByPartRequest': {
                        'mouserPartNumber': part_number,
                        'partSearchOptions': option,
                    }
                }

        return body

    def part_search(self, part_number, option='None'):
        '''Mouser Part Number Search '''

        kwargs = {
            'part_number': part_number,
            'option': option,
        }

        self.body = self.get_body(**kwargs)

        if self.api_key:
            return self.run(self.body)
        else:
            return False
