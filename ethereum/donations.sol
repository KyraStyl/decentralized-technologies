// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

contract Donations{

    //declarations
    address payable sudo; // the owner
    // the list of charities -- needs to be payable addresses 
    //in order to send the wei
    address payable[] private charities;
    address highestDonorAddress; // the best donor
    uint256 highestAmount; // the amount donated by best donor
    uint256 sumDonations; // the total amount of all donations made

    //modifier -- used for changing the visibility of functions
    //only for the owner
    modifier sudoOnly{
        require(msg.sender == sudo, "This is a sudo action!");
        _;
    }

    //event of donation -- used for the emit
    event Donation(address addrDon, uint don);

    //constructor -- initialize the variables of the class
    constructor (address payable[] memory _addrofcharities) {
        sudo = payable(msg.sender);
        charities = _addrofcharities;
        highestAmount = 0;
        sumDonations = 0;
    }

    //destructor -- can only be used by the owner/ "sudo" action
    function dctor() public sudoOnly{
        selfdestruct(sudo);
    }

    // can only be accessed by the owner/ "sudo" action
    // returns information (address, amountDonated) about the best donor
    function getBestDonor() public sudoOnly view returns (address, uint256){
        return (highestDonorAddress, highestAmount);
    }

    //==== public function - 1st variation ====//
    //accepts only the address where the wei would go, and the ID of the charity
    //in which will be transferred the 10% of the total amount
    function donate(address payable rest, uint8 chID) public payable returns (uint256){
        // perform the appropriate checks
        require(msg.value<=msg.sender.balance, "User does not have the required amount to do the transfer requested!");
        uint256 size = charities.length;
        require(chID < size && chID >=0, "This charity does not exist.");
        uint256 amountToDonate = msg.value/10;

        create_and_emit_Donation(rest, amountToDonate, chID);
        return amountToDonate;
    }

    //==== public function - 2nd variation ====//
    //accepts the address where the wei would go, the ID of the charity,
    //and also the amount of the wei that would be transferred to the charity
    function donate(address payable rest, uint256 amount, uint8 chID) public payable {
        // perform the appropriate checks
        require(msg.value<=msg.sender.balance, "User does not have the required amount to do the transfer requested!");
        require(amount >= msg.value/100, "Amount of donation must be at least 1%");
        require(amount <= msg.value/2, "Amount of donation can't be more than half of the total transferred amount");
        uint256 size = charities.length;
        require(chID < size && chID >= 0, "This charity does not exist.");

        create_and_emit_Donation(rest, amount, chID);
    }

    //auxiliary function -- used in the above two functions
    //created to emit an event of Donation
    //params:
    //rest -> the address in which the wei will be transferred
    //chID -> the ID of charity to which the donation will be made
    //amount -> the amount that will be donated to the charity
    function create_and_emit_Donation(address payable rest, uint256 amount, uint8 chID) public payable {
        uint256 change = msg.value - amount;
        if (amount> highestAmount){
            highestAmount = amount;
            highestDonorAddress = msg.sender;
        }

        charities[chID].transfer(amount);
        rest.transfer(change);

        emit Donation(msg.sender, amount);
        sumDonations += amount;
    }



}
