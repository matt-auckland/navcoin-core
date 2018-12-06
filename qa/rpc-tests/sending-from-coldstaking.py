#!/usr/bin/env python3
# copyright (c) 2018 the navcoin core developers
# distributed under the mit software license, see the accompanying
# file copying or http://www.opensource.org/licenses/mit-license.php.
import decimal
from test_framework.test_framework import NavCoinTestFramework
from test_framework.util import *
#/TODO leave comments for how much is sent in each func call
class SendingFromColdStaking(NavCoinTestFramework):
    """Tests spending and staking to/from a spending wallet."""

    # set up num of nodes
    def __init__(self):
        super().__init__()
        self.setup_clean_chain = True
        self.num_nodes = 2
    # set up nodes
    def setup_network(self, split=False):
        self.nodes = self.setup_nodes()
        self.is_network_split = split

    def run_test(self):
        self.nodes[0].staking(False)

        """generate first 300 blocks to lock in softfork, verify coldstaking is active"""

        slow_gen(self.nodes[0], 100)
        print("generated 300 blocks")      
        # verify that cold staking has started
        assert(self.nodes[0].getblockchaininfo()["bip9_softforks"]["coldstaking"]["status"] == "started")
        slow_gen(self.nodes[0], 100)
        # verify that cold staking is locked_in
        assert(self.nodes[0].getblockchaininfo()["bip9_softforks"]["coldstaking"]["status"] == "locked_in")
        slow_gen(self.nodes[0], 100)
        # verify that cold staking is active
        assert(self.nodes[0].getblockchaininfo()["bip9_softforks"]["coldstaking"]["status"] == "active")

        """set up transaction-related constants and addresses"""

        # declare transaction-related constants
        SENDING_FEE= 0.00010000
        BLOCK_REWARD = 50
        # generate address owned by the wallet
        spending_address_public_key = self.nodes[0].getnewaddress()
        spending_address_private_key = self.nodes[0].dumpprivkey(spending_address_public_key)
        # declare third party addresses and keys
        staking_address_public_key = "mqyGZvLYfEH27Zk3z6JkwJgB1zpjaEHfiW"
        staking_address_private_key = "cMuNajSALbixZvApkcYVE4KgJoeQY92umhEVdQwqX9wSJUzkmdvF"
        address_Y_public_key = "mrfjgazyerYxDQHJAPDdUcC3jpmi8WZ2uv"
        address_Y_private_key = "cST2mj1kXtiRyk8VSXU3F9pnTp7GrGpyqHRv4Gtap8jo4LGUMvqo"
        # generate coldstaking address which we hold the spending key to
        coldstaking_address_spending = self.nodes[0].getcoldstakingaddress(staking_address_public_key, spending_address_public_key)

        """check wallet balance and staking weight"""

        # get wallet balance and staking weight before sending some navcoin
        balance_before_send = self.nodes[0].getbalance()
        staking_weight_before_send = self.nodes[0].getstakinginfo()["weight"]
        # check wallet staking weight roughly equals wallet balance
        assert(round(staking_weight_before_send / 100000000.0, -5) == round(balance_before_send, -5))

        """send navcoin to our coldstaking address, grab balance & staking weight"""

        # send funds to the cold staking address (leave some nav for fees) -- we specifically require
        # a transaction fee of minimum 0.002884 navcoin due to the complexity of this transaction
        self.nodes[0].sendtoaddress(coldstaking_address_spending, float(self.nodes[0].getbalance()) - 0.002884)
        # put transaction in new block & update blockchain
        slow_gen(self.nodes[0], 1)
        # create list for all coldstaking utxo recieved
        listunspent_txs = [n for n in self.nodes[0].listunspent() if n["address"] == coldstaking_address_spending]
        # asserts we have recieved funds to the coldstaking address
        assert(len(listunspent_txs) > 0)
        # asserts if amount recieved is what it should be; ~59812449.99711600 NAV
        assert(listunspent_txs[0]["amount"] == Decimal('59812449.99711600'))
        # grabs updated wallet balance and staking weight
        balance_post_send_one = self.nodes[0].getbalance()
        staking_weight_post_send = self.nodes[0].getstakinginfo()["weight"]

        """check balance decreased by just the fees"""
        
        #difference between balance after sending and previous balance is the same when block reward is removed
        # values are converted to string and "00" is added to right of == operand because values must have equal num of 
        #decimals
        assert(str(balance_post_send_one - BLOCK_REWARD) == (str(float(balance_before_send) - 0.00288400) + "00"))
        
        """check staking weight now == 0 (we don't hold the staking key)"""
        
        #sent ~all funds to coldstaking address where we do not own the staking key hence our 
        #staking weight will be 0 as our recieved BLOCK_REWARD navcoin isn't mature enough to count towards
        #our staking weight
        assert(staking_weight_post_send / 100000000.0 == 0)

        # test spending from a cold staking wallet with the spending key
        print(balance_post_send_one)
        # send funds to a third party address with sendtoaddress(), change sent to a newly generated change address
        #hence coldstakingaddress should be empty after
        self.nodes[0].sendtoaddress(address_Y_public_key, (float(balance_post_send_one) * float(0.5) - float(1)))
        slow_gen(self.nodes[0], 1)  
        # self.sync_all()

        balance_post_send_two = self.nodes[0].getbalance()
        #checks balance will not be less than ~half our balance before sending - this 
        #will occurs if we send to an address we do not own
        assert(balance_post_send_two - BLOCK_REWARD >= (float(balance_post_send_one) * float(0.5) - float(1)))
            
        # construct and send rawtx
        #need to resend to coldstaking, then re state listunspent_txs then can continue
        self.nodes[0].sendtoaddress(coldstaking_address_spending, balance_post_send_two - 1)
        slow_gen(self.nodes[0], 1)
        listunspent_txs = [ n for n in self.nodes[0].listunspent() if n["address"] == coldstaking_address_spending]
        # send funds to a third party address using a signed raw transaction    
        # get unspent tx inputs
        print(listunspent_txs[0])
        self.send_raw_transaction(decoded_raw_transaction = listunspent_txs[0], \
        to_address = address_Y_public_key, \
        change_address = coldstaking_address_spending, \
        amount = float(str(float(balance_post_send_two) - 2 - 0.01 - SENDING_FEE) + "00") \
        )

        slow_gen(self.nodes[0], 1)  
        # self.sync_all()


        balance_post_send_three = self.nodes[0].getbalance()
        print(balance_post_send_three)
        # we expect our balance more or less gone (less some fees)
        assert(balance_post_send_three - (BLOCK_REWARD * 2) <= 2)
        #minus block_reward * 2 because we only spent one utxo previously which did not contain
        #the previous blockreward either
        # generate some new coins and send them to our cold staking address
        slow_gen(self.nodes[0], 2)
        # self.sync_all()

        self.nodes[0].sendtoaddress(coldstaking_address_spending, self.nodes[0].getbalance() - 1)
        slow_gen(self.nodes[0], 1)
        # send to our spending address (should work)
        send_worked = False
        current_balance = self.nodes[0].getbalance()
        print("current balance call #1 returns | {}".format(current_balance))
        try:
            #fails here - unsupported operand type(s) for *: 'decimal.decimal' and 'float'
            self.nodes[0].sendtoaddress(spending_address_public_key, float(current_balance) * 0.5 - 1)
            slow_gen(self.nodes[0], 1)
            print("balance after sending half of total | {}".format(self.nodes[0].getbalance()))
            # our balance should be the same minus fees, as we own the address we sent to
            assert(self.nodes[0].getbalance() >= current_balance - 1 + BLOCK_REWARD) 
            send_worked = True
        except Exception as e:
            print(e)

        assert(send_worked == True)
        
        slow_gen(self.nodes[0], 1)
        # self.sync_all()


        # send to our staking address
        send_worked = False
        current_balance = self.nodes[0].getbalance()

        try:
            print("entered try block")
            self.nodes[0].sendtoaddress(staking_address_public_key, float(self.nodes[0].getbalance()) * 0.5 - 1)
            print("sent half balance to staking address")
            slow_gen(self.nodes[0], 1)
            print("called slow_gen()")
            # our balance should be half minus fees, as we dont own the address we sent to
            print("balance : {}".format(self.nodes[0].getbalance() - BLOCK_REWARD))
            print("current_balance variable value : {}".format(float(current_balance) * 0.5 - 1))
            assert(self.nodes[0].getbalance() - BLOCK_REWARD <= float(current_balance) * 0.5 - 1 + 2) 
            send_worked = True
        except Exception as e:
            print(e)
            
        assert(send_worked == True)
        

    def send_raw_transaction(self, decoded_raw_transaction, to_address, change_address, amount):
        # create a raw tx
        print("decoded_raw_transaction[\"amount\"] :", decoded_raw_transaction["amount"])
        print("amount :", amount)
        inputs = [{ "txid" : decoded_raw_transaction["txid"], "vout" : decoded_raw_transaction["vout"]}]
        print(decoded_raw_transaction)
        #output is less than 1 satoshi - fix
        outputs = { to_address : amount, change_address : float(decoded_raw_transaction["amount"]) - amount - float(round(0.01, 9)) }
        print(outputs)
        #len of decimals always 9+
        decimal_places_to_address = len((str(outputs[to_address]).split("."))[1])
        print(decimal_places_to_address)
        decimal_places_change_address = len((str(outputs[change_address]).split("."))[1])
        print(decimal_places_change_address)
        output_decimals_list = [{"decimals_length" : decimal_places_to_address, "address" : to_address}, {"decimals_length" : decimal_places_change_address, "address" : change_address}]
        for tx_output_decimals in output_decimals_list:
            if tx_output_decimals["decimals_length"] < 8:
                amount_of_zeros_needed = 8 - tx_output_decimals["decimals_length"]
                outputs[tx_output_decimals["address"]] = float(str(outputs[tx_output_decimals["address"]]) + ("0" * amount_of_zeros_needed))
            elif tx_output_decimals["decimals_length"] > 8:
                print("got here")
                #gets here correctly
                amount_of_zeros_not_needed = -1 * (8 - tx_output_decimals["decimals_length"])
                amount_sending = outputs[tx_output_decimals["address"]]
                outputs[tx_output_decimals["address"]] = float(str(amount_sending)[0 : (len(str(amount_sending)) - amount_of_zeros_not_needed)])
            else:
                continue

        print("to_address | sending:", outputs[to_address])
        print("change_address | sending:", outputs[change_address])
        print("total | sending:", outputs[to_address] + outputs[change_address])
        print("available balance: ", self.nodes[0].getbalance())
        #print("trying to send: ", outputs[0] + outputs[1])
        rawtx = self.nodes[0].createrawtransaction(inputs, outputs)

        # sign raw transaction
        signresult = self.nodes[0].signrawtransaction(rawtx)
        assert(signresult["complete"])

        # send raw transaction
        return self.nodes[0].sendrawtransaction(signresult['hex'])
        

if __name__ == '__main__':
    SendingFromColdStaking().main()


