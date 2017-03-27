from django.http.response import HttpResponse
import qrcode


def get_qrcode(request, oid):
    url = '%s://%s/#/view?oid=%s' % (request.scheme, request.get_host(), oid)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=7,
        border=4,
    )
    print('###', qr, '###')
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response
