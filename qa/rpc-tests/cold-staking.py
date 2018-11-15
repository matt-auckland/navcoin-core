#!/usr/bin/env python3
# Copyright (c) 2018 The Navcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from test_framework.test_framework import NavCoinTestFramework
from test_framework.util import *


class ColdStakingTest(NavCoinTestFramework):
    """Tests RPC commands and sending/receiving coins for cold staking addresses."""

    def __init__(self):
        super().__init__()
        self.setup_clean_chain = True
        self.num_nodes = 1

    def setup_network(self, split=False):
        self.nodes = self.setup_nodes()
        self.is_network_split = split

    def run_test(self):
        self.nodes[0].staking(False)
        slow_gen(self.nodes[0], 300)

        my_addr = self.nodes[0].getnewaddress()

        # Third party addresses and keys
        addr_A = "mqyGZvLYfEH27Zk3z6JkwJgB1zpjaEHfiW"
        priv_key_A = "cMuNajSALbixZvApkcYVE4KgJoeQY92umhEVdQwqX9wSJUzkmdvF"
        addr_B = "mrfjgazyerYxDQHJAPDdUcC3jpmi8WZ2uv"
        priv_key_B = "cST2mj1kXtiRyk8VSXU3F9pnTp7GrGpyqHRv4Gtap8jo4LGUMvqo"
        addr_C = "mn1zDkoxVgNL3FFF3fvgPE89P3eUCKSTDv"
        priv_key_C = "cPrX1VN4nkjArakKMRLHkmTAfroYU2py4MvMAHso1Uk9mpP5NUzF"
        addr_D = "mqNTqbA9hqupHvCPzucNv758FGJUqa1ggd"
        priv_key_D = "cUYjPmm1h8EmjgAFd57QZpYyHdmXjReHHG31hNBQBweg1PMXYjtD"



        cold_stk_addr_AB = self.nodes[0].getcoldstakingaddress(addr_A, addr_B)
        print("addr_A: " + addr_A + "\naddr_B: " + addr_B + "\ncold_stk_addr: " + cold_stk_addr_AB)

        # Verify the cold staking address is accepted
        self.nodes[0].getaccount(cold_stk_addr_AB)


        # Check malformed cold staking addresses

        # getcoldstakingaddress() tests go here



        """ Initialise coldstaking address where the wallet holds the spending address priv key (cold_stk_addr_my_spending) """
        cold_stk_addr_my_spending = self.nodes[0].getcoldstakingaddress(addr_A, my_addr)
        beginning_balance_my_wallet = self.nodes[0].getbalance()
        beginning_weight_my_wallet = self.nodes[0].getstakinginfo()["weight"]

        # Check wallet weight roughly equals wallet balance
        assert(round(beginning_weight_my_wallet / 100000000.0, -5) == round(self.nodes[0].getbalance(), -5))

        # Send funds to the cold staking address (leave some NAV for fees)
        self.nodes[0].sendtoaddress(cold_stk_addr_my_spending, self.nodes[0].getbalance() - 1)

        beginning_balance_my_spending = self.nodes[0].getbalance()
        beginning_weight_my_spending = self.nodes[0].getstakinginfo()["weight"]

        # Check the wallet amount is unchanged (less fees)
        assert(beginning_balance_my_spending >= beginning_balance_my_wallet - 1)
        # Check the wallet weight is reduced
        assert(beginning_weight_my_spending / 100000000.0 <= 1)


        # Test spending from a cold staking wallet with the spending key
            # Send almost all funds to a third party address (leave some NAV for fees)
        self.nodes[0].sendtoaddress(addr_C, beginning_balance_my_spending - 1)

        # Check the remaining balance in the wallet
        assert(self.nodes[0].getbalance() <= 1)
        # Check the remaining wallet weight is unchanged
        assert(self.nodes[0].getstakinginfo()["weight"] / 100000000.0 >= beginning_weight_my_spending / 100000000.0 - 1)



        slow_gen(self.nodes[0], 300)

        """ Initialise coldstaking addresses where the wallet is the staking address (cold_stk_addr_my_staking) """
        cold_stk_addr_my_staking = self.nodes[0].getcoldstakingaddress(my_addr, addr_B)
        beginning_balance_my_wallet = self.nodes[0].getbalance()
        beginning_weight_my_wallet = self.nodes[0].getstakinginfo()["weight"]

        # Check wallet weight roughly equals wallet balance
        assert(round(beginning_weight_my_wallet / 100000000.0, -5) == round(self.nodes[0].getbalance(), -5))

        # Send funds to the cold staking address (leave some NAV for fees)
        self.nodes[0].sendtoaddress(cold_stk_addr_my_staking, beginning_balance_my_wallet - 1)

        beginning_balance_my_staking = self.nodes[0].getbalance()
        beginning_weight_my_staking = self.nodes[0].getstakinginfo()["weight"]
        print(beginning_balance_my_staking)
        print(beginning_weight_my_staking)

        # Check the wallet amount is reduced
        assert(beginning_balance_my_staking <= 1)
        # Check the wallet weight is unchanged (less fees)
        assert(beginning_weight_my_staking / 100000000.0 >= beginning_weight_my_wallet / 100000000.0 - 1)


        # Test spending from a cold staking wallet with the staking key
            # Send almost all funds to a third party address (leave some NAV for fees)
        try:
            self.nodes[0].sendtoaddress(addr_C, beginning_balance_my_wallet - 1)
            raise ValueError("Error should be thrown for spending from a staking wallet!")
        except JSONRPCException as e:
            assert("Insufficient funds" in e.error['message'])

        # Check the remaining balance in the wallet is unchanged
        assert(self.nodes[0].getbalance() == beginning_balance_my_staking)
        # Check the remaining wallet weight is unchanged
        assert(self.nodes[0].getstakinginfo()["weight"] / 100000000.0 >= beginning_weight_my_staking / 100000000.0 - 1)



if __name__ == '__main__':
    ColdStakingTest().main()
