from tortoise import fields, Model
from tortoise.fields import DatetimeField


class Site(Model):
    id = fields.IntField(pk=True)
    site = fields.CharField(max_length=255)
    rank = fields.IntField(unique=True)
    url = fields.CharField(max_length=255)
    created_time = fields.DatetimeField(auto_now_add=True)

    # Headers experiment
    experiment_headers = fields.CharField(max_length=255, null=True)
    experiment_headers_state = fields.CharField(max_length=50, null=True)
    experiment_headers_start_time = DatetimeField(null=True)
    experiment_headers_end_time = DatetimeField(null=True)

    # Inclusions experiment
    experiment_inclusions = fields.CharField(max_length=255, null=True)
    experiment_inclusions_state = fields.CharField(max_length=50, null=True)
    experiment_inclusions_start_time = DatetimeField(null=True)
    experiment_inclusions_end_time = DatetimeField(null=True)

    # CXSS experiment
    experiment_cxss = fields.CharField(max_length=255, null=True)
    experiment_cxss_state = fields.CharField(max_length=50, null=True)
    experiment_cxss_start_time = DatetimeField(null=True)
    experiment_cxss_end_time = DatetimeField(null=True)

    # PMSecurity experiment
    experiment_pmsecurity = fields.CharField(max_length=255, null=True)
    experiment_pmsecurity_state = fields.CharField(max_length=50, null=True)
    experiment_pmsecurity_start_time = DatetimeField(null=True)
    experiment_pmsecurity_end_time = DatetimeField(null=True)

    class Meta:
        table = "sites"

    def __str__(self):
        return f"{self.site} (Rank: {self.rank})"
