Documentation
=============

OCDS export is a project that dumps release packages from Openprocurement Data to json files and sends it to the S3.

Building
--------

Use following commands to build :

``python bootstrap.py``

``bin/buildout -N``

``bin/supervisord``

Usage
--------
::

    bin/packages -n 2048

Each generated json will include 2048 releases. Default value is 4096.

::

    bin/packages -d 2016-09-09 -d 2016-09-10

Generate packages only for data which dateModified is between 2016-09-09 and 2016-09-10.

::

    bin/packages -contracting

Generate packages including contracts from contracting module.

All packages are automatically sended to S3. You can configure your own bucket in **templates/bridge.yaml**. Also you can view OpenProcurement Data in OCDS format at ocds.prozorro.openprocurement.io

Timers
------
To run export repeatedly you can use **systemd-timers**. Configuration for this is at **/etc** direcrory.
Commands to execute:
::

    cd etc
    sudo cp export.service /lib/systemd/system/export.service
    sudo cp export.timer /lib/systemd/system/export.timer
    sudo systemctl start export.timer

Now OCDS export will start every friday at 03:00 AM.

Extensions
----------

OCDS export also provides dump with extensions which held in **JsonPatch** format in **/patches** directory. Description for each of it:

1. **MEAT**: Features of tender.
2. **Additional Contacts**: List of additional contact points for the organization.
3. **Auction**: Auction object which shows all auction properties of lots and tender.
4. **Bid**: For representing a bid in response to the tender or qualification stage in this contracting process.
5. **Pending Cancellation**: Yes or No field showing  whether a tender/lot is pending for cancellation.
6. **Complaints**: Complaints to tender conditions and their resolutions.
7. **Contract ID**: Number of the contract, auto generated.
8. **Contract Number**: Editable number of the contract.
9. **Contract Suppliers**: Description of the supplying organization, auto-generated.
10. **Delivery**: (address, date, location).
11. **Eligibility**: (eligible, selfEligible): Confirms compliance of eligibility criteria set by the procuring entity/customer in the tendering documents.
12. **Enquiries**: A question related to this contracting process, generally sent during the enquiry period.
13. **Guarantee**: A sum of money which the Economic Operator  may set out in tender documentation and which the Participant (Award of Tender/Lot) shall pay in case of a refusal to sign the Contract, or in other cases foreseen in the Law.
14. **Linked Document**: Identifier of the item that the document belongs to.
15. **Lot**: Lot related to tender.
16. **Negotiation**: Cause of negotiations. See Article 35 of the Law of Ukraine "On Public Procurement". Required for openprocurement.limited.
17. **Procurement Method Details**: (procurementMethodType) Type of Open Procurement procedure.
18. **Qualification**: Prequalification related objects.
19. **Shortlisted Firm**: A list of firms which can register bids on the second stage of the competitive dialogue procedure.
20. **Tender ID**: The tender identifier to refer tender to in "paper" documentation. TenderID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
21. **Unit Code**: UN/CEFACT Recommendation 20 unit code.
22. **Value Added Tax**: A Yes/No field to indicate whether the value tax was included.
