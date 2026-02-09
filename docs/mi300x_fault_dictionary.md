# MI300x Fault Dictionary

_Converted from PDF: 2026-02-08_

---

## Overview

This document tabulates **Critical** and **Major** severity hardware faults from ILOM (Integrated Lights Out Manager), plus **Other** (e.g. Minor) hardware faults. It is intended for triage, repair, and maintenance of MI300x hardware.

**Context.** ILOM is purpose-built hardware that monitors hardware health. It maintains logs of *Open Problems* (faults, alerts, and defects) on the system. With the Hardware Fault Event feature, customers can receive these fault details for their hardware. Each entry below includes a short name and description; severity is assigned by the hardware teams.

> **Note.** These lists reflect common understanding and analysis across OCI teams for a particular platform; understanding and contents may change over time.  
> The **Fault ID** in the tables below corresponds to **`fmaMessageID`** in `com.oraclecloud.hardwarefault.ilomfault`-type events when the Hardware Fault event feature is enabled.

---

## Critical and Major Severity Hardware Faults (ILOM)

Columns: **#** | **Fault ID** | **Name** | **Description** | **Severity**

---

 1     SPENV-    alert.chassis.        ILOM has detected that a board is missing. Unable to Power On. The board is unavailable.                                       Critical
       8002-6K   config.gbb.
                 missing

 2     SPENV-    alert.chassis.        GPU is missing. Unable to Power On. System will not power on.                                                                 Critical
       8002-7F   config.gpu.
                 missing

 3     SPENV-    alert.chassis.        Retimer card is missing. Unable to Power On. System will not power on.                                                         Critical
       8002-F0   config.retimer.
                 missing

 4     SPENV-    defect.chassis.spi.   The firmware on the Serial Peripheral Interface (SPI) flash has been corrupted. Reprovision Required. The system               Critical
       8001-A0   firmware.corrupt      is unable to power-on.

 5     SPENV-    fault.memory.         DDR5 PMIC Output voltage out of range. The host will reset. The system will be allowed to boot, but system                     Critical
       8002-H7   dimm.pmic-output-     performance may be impacted as the affected DIMMs are unavailable for use.
                 voltage-out-of-
                 range

 6     SPENV-    fault.memory.         The Power Management Integrated Circuit (PMIC) on a DDR5 DIMM has experienced an overtemperature failure.                      Critical
       8002-2U   dimm.pmic-            The host will reset. The system will panic and reset. The system will be allowed to boot, but system performance
                 overtemperature       may be impacted.

 7     SPENV-    fault.memory.         The Power Management Integrated Circuit (PMIC) on a DDR5 DIMM has detected an input overvoltage failure.                       Critical
       8002-0M   dimm.pmic-input-      ILOM is running, Host won’t start. The system will be powered down immediately and the system will not be allowed
                 overvoltage           to boot until the fault is cleared.

 8     ISTOR-    fault.io.disk.self-   A Disk Self-Test Failure has occurred. Reduced Storage OR Network Performance. The disk has failed self tests.                 Critical
       8000-2A   test-failure          Likely boot time only but if a bus is reset it will run a small amount of selftests … but we don’t know the criteria for this
                                       event.

 9     ISTOR-    fault.io.scsi.cmd.    ILOM fault manager has applied diagnosis to error reports indicating a non-recoverable media error was detected                Critical
       8000-4D   disk.dev.rqs.merr     by the device. Reduced Storage OR Network Performance. The service may have been lost or degraded. It is likely
                                       that continued operation will result in data corruption which may eventually cause the loss of service or the service
                                       degradation.

 10    ISTOR-    fault.io.scsi.cmd.    Indicates a non-recoverable drive failure was detected by the device while performing a command. Reduced                       Critical
       8000-5H   disk.dev.rqs.         Storage OR Network Performance. The service may have been lost or degraded. It is likely that continued operation
                 baddrv                will result in data corruption which may eventually cause the loss of service or the service degradation.

 11    ISTOR-    fault.io.scsi.disk.   ILOM diagnosis indicates a path to the disk device has been unconfigured due to transport instability. Reduced                 Critical
       8000-63   tran.unstable.leaf    Storage OR Network Performance. The I/O path to this device may have been lost or degraded.
12   ISTOR-    fault.io.disk.spare-   SMART health-monitoring firmware on the drive has detected the available spare space on disk device has been          Critical
     8000-7Y   space-exhausted        exhausted. Reduced Storage OR Network Performance. The disk has reached its end of life. Continued use of this
                                      disk will result in severe performance degradation. Risk of data loss or data corruption is imminent or is already
                                      occurring.

13   ISTOR-    fault.io.device.       The on-die temperature of the device controller has exceeded the critical limit established by the manufacturer.      Critical
     8000-DX   temperature-high-      Reduced Storage OR Network Performance. The system will continue to operate however system performance may
               critical               be impacted as the device will not be in use. The firmware on device will check the temperature at boot up and will
                                      abort the boot unless temperature is below critical limit.

14    SPGX-    alert.chassis.         Indicates that the OAM has not been detected or is missing during the initialization process. Unable to Power On.    Critical
     8000-13   config.oam.            The host will not power on. The OAM will need to be reseated or a new one installed.
               missing

15   SPGX-     alert.chassis.         ILOM has determined that OAMs have not been properly populated. Unable to Power On. Properly install the OCP         Critical
     8000-2H   config.oam.            Accelerator Modules. The result of GPU swapping during troubleshooting.
               unsupported

16   SPGX-     fault.chassis.gx.      ILOM has detected a corrupted ROM on a GPU. Unable to Power On. The host will not power on.                           Critical
     8000-ER   rom.corruption

17   SPGX-     fault.gpu.mem.         A uncorrectable ECC error in DRAM has occurred. The host will reset. Restart the applications that have stopped.      Critical
     8000-     ecc-uncontained
     GQ

18   SPGX-     fault.gpu.mem.         An uncorrectable ECC error in SRAM has occurred. Unable to Power On. The host has powered off.                        Critical
     8000-     ecc-uncorrectable
     HD

19   SPGXT     alert.chassis.gx.      Indicates that the GPU Base Board has an unknown manufacturer or model number. Unable to Power On. All of the         Critical
     AIL-      gbb.unknown            OAMs are unavailable for use.
     8000-2F

20   SPGXT     alert.chassis.         Fan Capacity is Deficient. Reduced CPU some cores may be disabled. May Auto-Clear                                     Critical
     AIL-      config.fan.
     8000-     capacity-deficient
     1W

21   SPGXT     alert.chassis.         Power Supplies is Deficient. Reduced Storage OR Network Performance. May Auto-Clear                                   Critical
     AIL-      power.supplies-
     8000-48   deficient

22   SPGXT     defect.chassis.gx.     indicates that firmware on the GBB has failed to boot. Unable to Power On. All of the OAMs are unavailable for use.   Critical
     AIL-      gbb.fw.boot-failed
     8000-5M

23   SPGXT     defect.chassis.gx.     Indicates that firmware on the GBB was not updated. Reprovision Required. The system will use the currently           Critical
     AIL-      gbb.fw.update-         installed firmware.
     8000-67   failed

24   SPGXT     defect.chassis.gx.     Indicates that firmware on the GBB could not be validated. Unable to Power On. All of the OAMs are unavailable for    Critical
     AIL-      gbb.fw.validation-     use.
     8000-7U   failed

25   SPGXT     fault.chassis.gx.      Indicates that the GBB health is at a critical level. Unable to Power On. All of the OAMs are unavailable for use.   Critical
     AIL-      gbb.device.health-
     8000-8L   critical

26   SPGXT     fault.chassis.gx.      Indicates a failure on the GBB FPGA. Unable to Power On. The board is unavailable.                                    Critical
     AIL-      gbb.fpga-failed
     8000-9G

27   SPGXT     fault.chassis.gx.      Indicates that the SPI bus on the GPU Base Board (GBB) has failed. Unable to Power On. All of the OAMs are            Critical
     AIL-      gbb.spi-bus-failed     unavailable for use.
     8000-C0

28   SPGXT     fault.chassis.gx.      PCIE CRC error was encountered on an nvswitch. Unable to Power On. The host will not power on.                        Critical
     AIL-      pcie.crc-error
     8000-DT

29   SPGXT     fault.chassis.gx.      Problem with the IOB has caused a PCIE reset failure. Reduced CPU, some cores may be disabled. All                    Critical
     AIL-      pcie.iob-reset-        downstream devices will be unavailable.
     8000-E6   assert

30   SPGXT     fault.chassis.gx.      PCIE switch has failed. Unable to Power On. All downstream devices will be unavailable.                               Critical
     AIL-      pcie.switch-failure
     8000-FN

31   SPGXT     fault.chassis.gx.      Indicates that a PCIe training error on a NVSwitch has occurred. Reduced CPU, some cores may be disabled. All         Critical
     AIL-      pcie.training-error    downstream devices will be unavailable.
     8000-HK

32   SPGXT     fault.chassis.gx.      PCIE uncorrectable error. Reduced CPU, some cores may be disabled. All downstream devices will be unavailable.        Critical
     AIL-      pcie.
     8000-JF   uncorrectable-
               error
33   SPGXT     fault.chassis.gx.     Problem in an upstream device has caused a PCIE reset failure. Reduced CPU, some cores may be disabled. All           Critical
     AIL-      pcie.upstream-        downstream devices will be unavailable.
     8000-     reset-assert
     KW

34   SPGXT     fault.chassis.gx.     detected a failure on the PDB 12v supply. Unable to Power On. The board is unable to provide power.                   Critical
     AIL-      pdb.p12v-power-
     8000-L1   failed

35   SPGXT     fault.chassis.gx.     ILOM has detected a power good failure on the tail node. Unable to Power On. The host will not power on.              Critical
     AIL-      power-good-failed
     8000-
     MU

36   SPGXT     fault.chassis.gx.     GPU Temperature Fail. Reduced CPU some cores may be disabled. May Auto-Clear                                          Critical
     AIL-      temp.fail
     8000-N7

37   SPGXT     fault.io.pcie.data-   PCIe Link Layer Inactive. Reduced Storage OR Network Performance. The system is unable to power on.                   Critical
     AIL-      link-layer-inactive
     8000-
     PM

38   SPENV-    defect.chassis.       the firmware of the Storage Enclosure Processor (SEP) located on the disk backplane is outdated and requires an       Critical
     8002-JU   memory.lb.sep.fw.     update. Reduced Storage OR Network Performance. (Lenovo Only) Upgrade to the latest SEP firmware on the disk
               update-needed         backplane.

39   SPENV-    fault.chassis.        an update of the Storage Enclosure Processor (SEP) firmware on the disk backplane has failed. Reduced Storage         Critical
     8002-K8   memory.lb.sep.fw.     OR Network Performance. (Lenovo Only) Replace disk backplane if upgrade of the SEP firmware has failed.
               update-failed

40   SPENV-    fault.memory.         A DIMM has reached an Unrecoverable Overtemperature. Validate there are no cooling issues present. The host           Critical
     8002-LM   dimm.unr-             will reset. A memory DIMM has exceeded the non-recoverable temperature limit. The system will immediately power
               overtemperature       off.

41   SPENV-    defect.chassis.       LB SPI Firmware Corrupt. The host will reset. The system is unable to power-on. The system should be re-              Critical
     8001-K1   memory.lb.spi.        provisioned using the HoPS process which will automatically attempt to fix the firmware on the SPI flash.
               firmware.
               corrupted

42   SPENV-    fault.chassis.        LB SPI Firmware Failed. ILOM won't start. The system is unable to power-on. Replacement of the Motherboard is         Critical
     8001-     memory.lb.spi.        necessary.
     LW        failed

43   SPENV-    alert.chassis.        An invalid power supply configuration has been detected. Configuration Issue after Repair. The system may be          Critical
     8000-2N   config.psu.           unable to power on.
               unsupported

44   SPENV-    fault.chassis.        A device necessary to support a configuration has failed. ILOM is running Host won’t start. The system may be         Critical
     8000-9M   device.fail           unable to boot.

45   SPGXT     fault.chassis.gx.     Indicates that the GBB health is at a critical level. Unable to Power On. All of the OAMs are unavailable for use.   Critical
     AIL-      gbb.i2c-bus-failed
     8000-AV

46   SPENV-    fault.chassis.        The Field Programmable Gate Array (FPGA) has detected a malfunctioning component and has powered-off the              Critical
     8000-D1   domain.boot.          system. Unable to Power On. The system is unable to power-on. (Voltage Faults)
               power-off-
               unexpected

47   SPENV-    fault.chassis.        Number of boot retries has exceeded limit. The Host will not boot. The system is unable to complete the boot          Critical
     8000-     domain.boot.          sequence.
     EW        retries-failed

48   SPENV-    fault.chassis.        The Field-Programmable Gate Array (FPGA) has detected the system standby was powered off unexpectedly.                Critical
     8000-FF   domain.boot.          Unable to Power On. The system is unable to power on.
               standby-power-
               off-unexpected

49   SPENV-    fault.chassis.fw.     The BIOS has detected that the platform information structure (SPI flash) is invalid. Unable to Power On. The         Critical
     8000-     platform-info.        system is unable to power on. BIOS does not have valid platform information to boot properly.
     GK        invalid

50   SPENV-    fault.chassis.mb.     A failure with a voltage regulator on the motherbord has been detected. Unable to Power On. The server will be        Critical
     8000-H9   volt_reg_failed       unable to boot.

51   SPENV-    fault.chassis.        A serial peripheral interface error. Unable to Power On. The system is unable to power-on.                            Critical
     8000-JN   memory.spi.error

52   SPENV-    fault.chassis.        A power source has failed or is not available to the server. Reduced power or cooling to the Server. The host OS      Critical
     8000-LT   power.fail            may not be able to boot if there is insufficient power.

53   SPENV-    alert.chassis.        PSU Mix Models Identified. Configuration Issue after Repair. The system may be unable to power on. The power          Critical
     8001-     config.psu.mixed-     supply configuration must utilize the same PSU model. Install power supplies with matching models / wattage output
     W9        models-identified

54   SPENV-    alert.chassis.        PSU Mix Models Unidentified. Configuration Issue after Repair. The system may be unable to power on. The power        Critical
     8001-XT   config.psu.mixed-     supply configuration must utilize the same PSU model. Install power supplies with matching models / wattage output
               models-
               unidentified
55   SPENV-    alert.chassis.        All retimer cards are missing.                                                                                          Critical
     8002-A9   config.retimer.all-
               missing               (We will get one of these for the whole tail node if all 8 retimer cards are missing) . Unable to Power On. System
                                     will not power on.

56   SPENV-    alert.chassis.        Retimer card's cable is missing. Unable to Power On. System will not power on.                                         Critical
     8002-EL   config.retimer.
               cable.missing

57   SPGX-     defect.chassis.gx.    indicates that firmware on the OAM has failed to boot. All of the OAMs are unavailable for use.                         Critical
     8000-4P   oam.fw.boot-failed

58   SPGX-     defect.chassis.gx.    Indicates that firmware on the OAM was not updated. Reprovision Required. The system will use the currently             Critical
     8000-5A   oam.fw.update-        installed firmware.
               failed

59   SPGX-     defect.chassis.gx.    Indicates that firmware on the OAM could not be validated. All of the OAMs are unavailable for use.                     Critical
     8000-6S   oam.fw.validation-
               failed

60   ILOM-     defect.ilom.fdd.      ILOM Fault Diagnosis Daemon (FDD) encountered an error parsing its diagnosis rules files. ILOM Impacted No            Critical
     8000-LL   unparsable_diagn      Impact to the Host. Some faults will not be automatically diagnosed.
               osis_rules

61   ILOM-     fault.chassis.        The Service Processor power-on self test has detected a problem. . ILOM unable to Initialize Host may not start.        Critical
     8000-4T   device.sppost         The Service Processor may not be able to perform necessary functions to power on monitor or manage the
                                     system. Reset the SP.

62   SPGX-     fault.chassis.gx.     The HMC (or its 3.3v coin battery) is non-functional. Unable to Power On. The HMC is not ready and the system is        Critical
     8000-75   hmc.failed            unable to power on

63   SPGX-     fault.chassis.gx.     GPU NVLink failure has occurred. Reduced CPU, some cores may be disabled. All of the OAMs are unavailable             Critical
     8000-8E   nvlink.error          for use.

64   SPGX-     fault.chassis.gx.     GPU NVSwitch is hanging. Unable to Power On. The host will not power on.                                                Critical
     8000-9J   nvswitch.
               operation-
               suspended

65   SPGX-     fault.chassis.gx.     GPU NVSwitch is unavailable. Unable to Power On. All of the OAMs are unavailable for use.                              Critical
     8000-A2   nvswitch.
               unavailable

66   SPGX-     fault.chassis.gx.     Indicates that the OAM health is at a critical level. Unable to Power On. All of the OAMs are unavailable for use.     Critical
     8000-CX   oam.device.
               health-critical

67   SPGX-     fault.chassis.gx.     Indicates that an OAM has experienced an uncorrected error. Unable to Power On. All of the OAMs are unavailable        Critical
     8000-D4   oam.uncorrected       for use.

68   ISTOR-    fault.io.scsi.cmd.    ILOM fault manager has applied diagnosis to error reports indicating a non-recoverable hardware failure was             Critical
     8000-3P   disk.dev.rqs.derr     detected by the disk device. Reduced Storage OR Network Performance. The device has failed. The service may
                                     have been lost or degraded. It is likely that continued operation will result in data corruption which may eventually
                                     cause the loss of service or the service degradation." RunTime.

69   SPINTE    alert.chassis.boot.   PMC Patch Failed. Reprovision Required. Platform services will automatically perform a power-cycle of the system        Critical
     L-8000-   intel.pmc-patch-      and clear this event.
     12        failed-
               nonserviceable

70   SPENV-    alert.chassis.        All retimer cards have no power. Unable to Power On. System will not power on.                                         Critical
     8002-     config.retimer.all-
     CN        no-power

71   SPENV-    alert.chassis.        The order in which retimer cables are connected is wrong. The Host will not boot. The Host will not boot               Critical
     8002-     config.retimer.
     DG        cable-order-wrong

72   SPENV-    alert.chassis.        The Field Programmable Gate Array (FPGA) has detected a power-on request that was denied by the service                 Critical
     8000-QL   domain.boot.          processor. ILOM is running Host won’t start. The system is unable to power on.
               power-on-failed

73   SPINTE    alert.chassis.        A warm reset was unsuccessful in clearing IERR condition. No direct impact look for associated events. Platform       Critical
     L-8000-   domain.intel.ierr-    services will automatically power-cycle the server.
     2J        persistent-
               nonserviceable

74   SPENV-    alert.chassis.fw.     The deferred update of the system BIOS has failed. No direct impact look for associated events. The BIOS update       Critical
     8000-39   bios-upgrade-         may need to be manually performed as part of an overall ILOM update.
               failure

75   SPENV-    alert.chassis.        ILOM was able to access the serial peripheral (SPI) flash device but the write was blocked or the resulting image       Critical
     8000-4L   memory.spi.           was corrupted. No direct impact look for associated events. The system is unable to power on.
               update.failure

76   SPENV-    alert.chassis.        Power Inadequate. Reduced power or cooling to the Server. The system will not be allowed to power-on.                   Critical
     8000-M0   power.inadequate

77   SPENV-    alert.chassis.sp.     System has detected invalid or corrupt firmware in the FPGA or ILOM power state. Reprovision Required. The             Critical
     8000-5G   firmware-invalid      system is unable to power on.
78   SPENV-    alert.chassis.         The ambient temperature of the system has exceeded established thresholds. Reduced power or cooling to the             Critical
     8000-6V   temp.warn              Server. The system continues to operate provided the internal temperature range does not exceed threshold for
                                      adequate cooling.

79   SPINTE    alert.cpu.intel.       The Platfom Controller Hub (PCH) is not compatible with the installed processor. Reduced CPU some cores may           Critical
     L-8007-   pch_incompatible       be disabled. The system will be unable to power on.
     7J

80   SPINTE    alert.cpu.intel.       The Ultrapath Interconnect Initialization Code (UPIRC) has detected a global error. No direct impact look for         Critical
     L-8000-   ultrapath.global-      associated events. The system can not be powered on in this condition.
     8D        error-posted-
               nonserviceable

81   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected that the DCPMM DIMMs partitions are not the same size.                   Critical
     L-8007-   dimm.3dx.              Reduced Memory some dimms may be disabled. The system is unable to power on.
     95        partition-size-
               mismatch

82    SPINTE   alert.memory.intel.    The Memory Reference Code (MRC) has detected that no system memory is available. Reduced Memory some                  Critical
     L-8007-   dimm.memory-           dimms may be disabled. The system is unable to power on.
     AP        none

83   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected Memory DIMMs of different types. Reduced Memory some                     Critical
     L-8000-   dimm.mismatch          dimms may be disabled. The system will be unable to boot and no video output to the Host console. A fatal error will
     K2                               result in the entire memory subsystem to be unusable.

84   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected a mixture of 3DX DIMMS and UDIMMs. Reduced Memory some                   Critical
     L-8000-   dimm.mixed-3dx-        dimms may be disabled. The system will be unable to boot and no video output to the Host console. A fatal error will
     LX        udimm                  result in the entire memory subsystem to be unusable.

85   SPINTE    alert.memory.intel.    An unsupported memory configuration using DDR4 DIMM(s) that are below 32-GB in size has been detected.                Critical
     L-8001-   mrc.ddr4-              Configuration Issue after Repair. The system may be unable to boot.
     0S        capacity-under-
               limit

86   SPINTE    alert.memory.intel.    The DDR4 DIMM type is an unsupported configuration in the current memory mode. Configuration Issue after              Critical
     L-8001-   mrc.ddr4-type-         Repair. The system may be unable to boot.
     15        incompatible-with-
               memory-mode

87   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected a global error. No direct impact look for associated events. The        Critical
     L-8001-   mrc.global-error-      system is unable to be powered on in the presence of this condition.
     4H        posted-
               nonserviceable

88   SPINTE    alert.memory.intel.    The processor has determined the capacity ratio between a DDR4 DIMM and DCPMM DIMM is outside the                      Critical
     L-8001-   mrc.invalid-           recommended range. Configuration Issue after Repair. The system may be unable to boot.
     5D        nearmem-farmem-
               ratio

89   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has determined that DIMM sockets are not using the same memory mode.                  Critical
     L-8001-   mrc.mixed-             Configuration Issue after Repair. The system may be unable to boot.
     6Y        memory-modes-
               unsupported

90   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has determined that a processor is unable to detect any DIMM's installed that          Critical
     L-8007-   mrc.no-dimm-on-        are associated with that processor. Reduced Memory some dimms may be disabled. The system is unable to boot.
     MJ        socket

91   SPINTE    alert.memory.intel.    The Data Center Persistent Memory Modules (DCPMM) installed across all DIMM sockets don't have the same                Critical
     L-8001-   mrc.socket-ddrt-       capacity. Configuration Issue after Repair. The system may be unable to boot.
     9Q        capacity-
               mismatch

92   SPINTE    alert.memory.intel.    The memory topology is not symmetrical between memory controllers. Configuration Issue after Repair. The              Critical
     L-8001-   mrc.topology-not-      system may be unable to boot.
     A4        symmetrical

93   SPINTE    defect.chassis.fw.     The Platform Controller Hub (PCH) PMC patch did not load properly. Unable to Power On. The system is unable to        Critical
     L-8001-   intel.pmc-patch.       be powered on when the PCH is in this condition.
     D2        invalid

94   SPINTE    defect.chassis.        The Platform Controller Hub (PCH) was unable to service a power-on request even after it was reset. Unable to         Critical
     L-8001-   intel.pch.             Power On. The system is unable to be powered on when the PCH is in this condition.
     FE        unresponsive

95   SPINTE    defect.cpu.intel.      A problem within the BIOS code has been detected. Unable to Power On. The system is unable to be powered on.          Critical
     L-8001-   bios
     GJ

96   SPINTE    defect.cpu.intel.rc.   Fatal Internal Error. Reprovision Required. The system is unable to boot. Upgrade to the latest ILOM/BIOS              Critical
     L-8009-   lib-internal-error     Firmware.
     G9

97   SPINTE    defect.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected that the Ultrapath could not transition to full         Critical
     L-8001-   ultrapath.full-        speed because an unsupported UPI link speed parameter within UPIRC has been encountered. Unable to Power
     HA        speed-transition       On. The system is unable to be powered on.
98    SPINTE    defect.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has determined that the UPI link speed is not supported by          Critical
      L-8007-   ultrapath.link-       firmware. The Host will not boot. The system is unable to boot.
      RA        speed-
                unsupported

99    SPINTE    defect.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has detected an internal error in the minimum path setup.          Critical
      L-8001-   ultrapath.minpath-    Unable to Power On. The system is unable to be powered on as the processors and Ultrapath links are unusable.
      K5        internal-failure

100   SPINTE    defect.cpu.intel.     The Ultrapath Interconnect Code (UPIRC) has detected an internal error. Unable to Power On. The system is            Critical
      L-8001-   ultrapath.sanity-     unable to be powered on as the processors and Ultrapath links are unusable.
      LS        check

101   SPINTE    defect.cpu.intel.     The Ultrapath Interconnect Code (UPIRC) has detected the Ultrapath Interconnect (UPI) topology data is invalid.       Critical
      L-8001-   ultrapath.            Unable to Power On. The system is unable to be powered on as the processors and Ultrapath links are unusable.
      M3        topology_invalid_
                data

102   SPINTE    defect.cpu.intel.     An unsupported Ultrapath topology has been detected. Unable to Power On. The system is unable to be powered          Critical
      L-8001-   ultrapath.            on.
      QH        unsupported-
                topology

103   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected an array access out-of-bounds. Unable to Power On. The                  Critical
      L-8001-   intel.array-out-of-   system is unable to be powered on.
      RR        bounds

104   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected that the System Address Decoder (SAD) rules encountered a                Critical
      L-8001-   intel.dimm.sad-       configuration error. ILOM Impacted No Impact to the Host. A fatal error will result in the entire memory subsystem
      UC        rules-config-error    to be unusable. The system will be unable to boot and no video output to the Host console.

105   SPINTE    defect.memory.        DDR Frequency Not Found. Reprovision Required. The system is unable to boot. Upgrade to the latest ILOM/BIOS          Critical
      L-8009-   intel.mrc.ddr-        Firmware.
      JF        frequency-not-
                found

106   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected the number of Integrated memory controllers (IMC) has                    Critical
      L-8002-   intel.mrc.imc-        exceeded the limit. Unable to Power On. The system is unable to be powered on.
      2Y        number-exceeded

107   SPINTE    defect.memory.        The Memory Reference Code (MRC) has encountered an internal memory management error. The Host will not               Critical
      L-8007-   intel.mrc.internal-   boot. The system is unable to boot.
      WY        semaphore-error

108   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected an invalid boot mode. Unable to Power On. The system is                 Critical
      L-8002-   intel.mrc.invalid-    unable to be powered on.
      4S        boot-mode

109   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected an invalid access to a register. Unable to Power On. The                Critical
      L-8002-   intel.mrc.invalid-    system is unable to be powered on.
      55        reg-access

110   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected an invalid subboot mode request. Unable to Power On. The                Critical
      L-8002-   intel.mrc.invalid-    system is unable to be powered on.
      6P        subboot-mode

111   SPINTE    defect.memory.        The Memory Reference Code (MRC) has encountered a library internal error. The Host will not boot. The system is      Critical
      L-8007-   intel.mrc.lib-        unable to boot.
      XD        internal-error

112   SPINTE    defect.memory.        The Memory Reference Code (MRC) could not lookup ODT structure. Unable to Power On. The system is unable             Critical
      L-8002-   intel.mrc.odt-        to be powered on.
      7A        struct-lookup-
                failed

113   SPINTE    defect.memory.        The Memory Reference Code (MRC) has encountered an internal memory allocation error. The Host will not boot.         Critical
      L-8007-   intel.mrc.out-of-     The system is unable to boot.
      YH        heap-memory

114   SPINTE    defect.memory.        The Memory Reference Code (MRC) has determined that the memory DIMM population rules are invalid. The Host           Critical
      L-8008-   intel.mrc.            will not boot. The system is unable to boot.
      1T        population-rules-
                table-invalid

115   SPINTE    defect.memory.        The Memory Reference Code (MRC) has determined that the memory DIMM population rules for a socket are                 Critical
      L-8008-   intel.mrc.socket-     unavailable. The Host will not boot. The system is unable to boot.
      29        population-rules-
                nomatch

116   SPINTE    defect.memory.        VDD Out of Range. Reprovision Required. The system is unable to boot. Upgrade to the latest ILOM/BIOS                 Critical
      L-8009-   intel.mrc.vdd-out-    Firmware.
      MU        of-range

117   SPENV-    fault.chassis.        Indicates insufficient cooling of server is due to multiple faulted or missing fan modules. The fan module            Critical
      8000-     config.fan.           configuration supported by the server can provide adequate cooling when one fan module is faulted or missing but
      RU        capacity-             not when more than one fan module has failed or is missing. Reduced power or cooling to the Server. The server
                insufficient          will be gracefully shutdown within 1 minute.

118   SPENV-    fault.chassis.dbp.    A lack of power to the disk backplane has been detected. The Host will not boot. The server will be unable to boot   Critical
      8000-88   power.fail            to the operating system.
119   SPENV-    fault.chassis.          Retimer card has an internal error. Unable to Power On. System will not power on.                                    Critical
      8002-     config.retimer.
      GV        failure

120   SPINTE    fault.chassis.          BIOS Hang. Unable to Power On. The service processor will shutdown the system and will be unable to be powered        Critical
      L-8002-   domain.boot.intel.      on.
      AE        me-noresp

121   SPINTE    fault.chassis.          MRC not successful. Unable to complete boot process. Unable to Power On. The system is unable to complete the        Critical
      L-8002-   domain.boot.intel.      boot process as the retry limit has been exceeded.
      CJ        mrc-failed

122   SPINTE    fault.chassis.          PCIE initialization failed to complete. Reduced Storage OR Network Performance. The platform services daemon         Critical
      L-8002-   domain.boot.intel.      will retry the boot sequence by issuing a power-off signal and a power-on request.
      DC        pcie-init-failed

123   SPINTE    fault.chassis.          The Demoted Warm Reset (DWR) process was unable to complete or is deadlocked. Reduced CPU some cores                 Critical
      L-8002-   domain.boot.intel.      may be disabled. The platform services daemon will retry the boot sequence by issuing a power-off signal and a
      EQ        reset-init-failed       power-on request.

124   SPINTE    fault.chassis.          The start of the boot process was unable to complete or is deadlocked. Unable to Power On. The platform services     Critical
      L-8002-   domain.boot.intel.      daemon will retry the boot sequence by issuing a power-off signal and a power-on request.
      F4        start-failed

125    SPINTE   fault.chassis.          The Ultrapath Interconnect (UPI) initialization Code was unable to complete or is deadlocked. Reduced CPU some       Critical
      L-8002-   domain.boot.intel.      cores may be disabled. The platform services daemon will retry the boot sequence by issuing a power-off signal
      GR        upirc-failed            and a power-on request.

126   SPINTE    fault.chassis.          Indicates processor internal errors (IERR) have been detected. Reduced CPU some cores may be disabled.              Critical
      L-8002-   domain.intel.ierr       Platform services will automatically power-cycle the server in an attempt to clear the fault.
      H3

127   SPINTE    fault.chassis.          Multiple processor internal errors have occurrred. Reduced CPU some cores may be disabled. Admin or User            Critical
      L-8002-   domain.intel.ierr-      needs to initiate a new boot process.
      JY        unrecoverable

128   SPENV-    fault.chassis.gx.       GPU Undetected. ILOM is running Host won’t start. The system will be unable to power on.                              Critical
      8001-6U   gpu.undetected

129   SPENV-    fault.chassis.          The internal temperature within the system has exceeded established thresholds. Reduced power or cooling to the      Critical
      8001-D6   temp.fail               Server. The system is unable to power on.

130   SPINTE    fault.cpu.intel.        The processor has encountered an Asynchronous DRAM Refresh (ADR) timeout. Reduced CPU some cores may                 Critical
      L-8008-   adr_timeout             be disabled. The system will panic and reset.
      3N

131   SPINTE    fault.cpu.intel.        The bus clock frequency for a processor has exceeded the fused threshold. Reduced CPU some cores may be              Critical
      L-8008-   bclk_error              disabled. The system will panic and reset.
      4G

132   SPINTE    fault.cpu.intel.bist.   The Memory Reference Code (MRC) has detected that a processor has failed the built-in self-test for all the cores.   Critical
      L-8002-   all-cores-failure       Reduced CPU some cores may be disabled. The system is unable to be powered on.
      KD

133   SPINTE    fault.cpu.intel.bist.   The Memory Reference Code (MRC) has detected that a processor has failed the built-in self-test on a single core.    Critical
      L-8002-   core-failure            Reduced CPU some cores may be disabled. The system is allowed to proceed with boot.
      LH

134   SPINTE    fault.cpu.intel.        The dispatcher of the Package Control Unit (PCU) on a processor has timed out. Reduced CPU some cores may            Critical
      L-8008-   disp_timeout            be disabled. The system will panic and reset.
      5L

135   SPINTE    fault.cpu.intel.        Direct Media Interface (DMI) training has failed to complete within specified time. Reduced CPU some cores may       Critical
      L-8002-   dmi_timeout             be disabled. The system will panic and reset.
      MA

136   SPINTE    fault.cpu.intel.        The idle state of the Package Control Unit (PCU) Finite-State Machine (FSM) on a processor has timed out.            Critical
      L-8008-   fsm_failures            Reduced CPU some cores may be disabled. The system will panic and reset.
      60

137   SPINTE    fault.cpu.intel.        An indeterminate processor error has occurred. Reduced CPU some cores may be disabled. The system will likely       Critical
      L-8002-   indeterminate           crash, but there are some cases where the UE could be just in the Customers App and therefore handled in
      NP                                userland, so its not 100%

138   SPINTE    fault.cpu.intel.        A processor has detected an internal fault. Reduced CPU some cores may be disabled. The system will panic and       Critical
      L-8002-   internal                reset. System performance may be impacted due to disabled core(s).
      P5

139   SPINTE    fault.cpu.intel.        A processor Built-in Self-Test (BIST) of its Last Level Cache (LLC) has timed out. Reduced CPU some cores may       Critical
      L-8008-   llc_timeout             be disabled. The system will panic and reset.
      7V

140   SPINTE    fault.cpu.intel.        A processor has detected a memory controller address/command parity uncorrectable error. Reduced CPU some            Critical
      L-8002-   mc_addr_cmd_pa          cores may be disabled. The system will most likely panic and reset.
      TX        rity_ue

141   SPINTE    fault.cpu.intel.        The memory controller on a processor has experienced a timeout in its Mesh2Mem logic. Reduced CPU some              Critical
      L-8002-   mc_timeout              cores may be disabled. The system will panic and reset.
      VR
142   SPINTE    fault.cpu.intel.     A processor has detected a memory controller uncorrectable error. Reduced CPU some cores may be disabled.          Critical
      L-8002-   mc_ue                The system will most likely panic and reset.
      W4

143   SPINTE    fault.cpu.intel.     The Power Control Unit (PCU) on a processor has detected excessive die temperature on the processor. Reduced        Critical
      L-8003-   overtemp             CPU some cores may be disabled. The system will panic and reset.
      0Q

144   SPINTE    fault.cpu.intel.     The processor has experienced a pkg C-state timeout or hang indicative of processor or UPI problems. Reduced        Critical
      L-8003-   pkgc_failure         CPU some cores may be disabled. The system will panic and reset.
      1C

145   SPINTE    fault.cpu.intel.     The processor has experienced a pkg S-state timeout or hang indicative of a processor or UPI failure. Reduced       Critical
      L-8003-   pkgs_failure         CPU some cores may be disabled. The system will panic and reset.
      34

146   SPINTE    fault.cpu.intel.     The Power Control Unit (PCU) on a processor has detected a power control failure. Reduced CPU some cores may        Critical
      L-8008-   pmax_failure         be disabled. The system will be unable to power on.
      8M

147   SPINTE    fault.cpu.intel.     The Power Control Unit (PCU) on a processor has detected a sideband timeout. Reduced CPU some cores may be          Critical
      L-8008-   sideband_timeout     disabled. The system will be unable to power on.
      98

148   SPINTE    fault.cpu.intel.     The Power Control Unit (PCU) on a processor has encountered a problem with clock synchronization. Reduced           Critical
      L-8008-   timestamp_counte     CPU some cores may be disabled. The system will be unable to power on.
      AU        r_sync

149   SPINTE    fault.cpu.intel.     During Boot Mode Processing more than 1 Intel TXT Agent has been detected. Reduced CPU some cores may be            Critical
      L-8003-   txt_config           disabled. The system is unable to be powered on.
      6J

150   SPINTE    fault.cpu.intel.     Processor UBOX General Error. The Host will not boot. The system is unable to power on. Replace the faulty           Critical
      L-8009-   ubox.general-error   processor at the earliest possible convenience.
      N7

151   SPINTE    fault.cpu.intel.   An invalid access to the System Configuration Controller (UBOX) on a processor has occurred. Reduced CPU              Critical
      L-8003-   ubox.              some cores may be disabled. The system is unable to be powered on.
      7E        invalid_cfg_access

152   SPINTE    fault.cpu.intel.     The System Configuration Controller (UBOX) has encountered a MasterLock timeout or System Management                 Critical
      L-8003-   ubox.timeout         Interrupt (SMI) Lock timeout. Reduced CPU some cores may be disabled. The system is unable to be powered on.
      9S

153   SPINTE    fault.cpu.intel.     An Ultrapath Interconnect (UPI) correctable link error has occurred. Reduced CPU some cores may be disabled.       Critical
      L-8003-   ultrapath.link_ce    The system is able to boot however system performance may be impacted.
      AA

154   SPINTE    fault.cpu.intel.     An Ultrapath Interconnect (UPI) link down error has occurred. Reduced CPU some cores may be disabled. This         Critical
      L-8003-   ultrapath.           fatal event will cause the system to reset as the UPI link is unusable.
      CP        link_down

155   SPINTE    fault.cpu.intel.     An Ultrapath Interconnect (UPI) CRC Link error has occurred. Reduced CPU some cores may be disabled. This          Critical
      L-8003-   ultrapath.           fatal event will cause the system to reset as the UPI link is unusable.
      DD        link_init_failure

156   SPINTE    fault.cpu.intel.     An Ultrapath Interconnect (UPI) uncorrectable link error has occurred. Reduced CPU some cores may be disabled.     Critical
      L-8003-   ultrapath.link_ue    The system will panic and reset. The processor will not be disabled.
      EH

157   SPINTE    fault.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has detected an error in the Ultrapath Interconnect (UPI) bus       Critical
      L-8003-   ultrapath.pbsp-      programming. Reduced CPU some cores may be disabled. The system is unable to power on as the processors
      H4        bus-failure          and Ultrapath links are unusable.

158   SPINTE    fault.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has detected a processor socket initialization failure.           Critical
      L-8003-   ultrapath.pbsp-      Reduced CPU some cores may be disabled. The system is unable to power on as the processors and Ultrapath
      JR        chkin-failure        links are unusable.

159   SPINTE    fault.cpu.intel.     A reset of the Power Control Unit (PCU) on a processor has timed out during processor initialization. Reduced CPU   Critical
      L-8008-   ultrapath.pcu-       some cores may be disabled. The system will be unable to power on.
      C7        reset-timeout

160   SPINTE    fault.cpu.intel.     An Ultrapath Interconnect (UPI) receiver failure has occurred. Reduced CPU some cores may be disabled. The         Critical
      L-8003-   ultrapath.rx_ue      system will panic and reset. The processor will not be disabled.
      ME

161   SPINTE    fault.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has detected that the system address decoder could not be          Critical
      L-8003-   ultrapath.sad-       setup. Reduced CPU some cores may be disabled. The system is unable to be powered on as the processors and
      NJ        setup                Ultrapath links are unusable.

162   SPINTE    fault.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) is unable to determine the processor topology. Reduced CPU        Critical
      L-8003-   ultrapath.           some cores may be disabled. The system is unable to be powered on as the processors and Ultrapath links are
      P2        topology-            unusable.
                discovery

163   SPINTE    fault.cpu.intel.     The Ultrapath Interconnect Reference Code (UPIRC) has detected an Ultrapath topology failure associated with the     Critical
      L-8003-   ultrapath.           UPI link. Reduced CPU some cores may be disabled. The system is unable to be powered on as the processors
      QX        topology_link_fail   and Ultrapath links are unusable.
                ure
164   SPINTE    fault.cpu.intel.    The Ultrapath Interconnect Reference Code (UPIRC) has detected an Ultrapath topology failure associated with the          Critical
      L-8003-   ultrapath.          processor socket. Reduced CPU some cores may be disabled. The system is unable to be powered on as the
      RP        topology_socket_f   processors and Ultrapath links are unusable.
                ailure

165   SPINTE    fault.cpu.intel.    An Ultrapath Interconnect (UPI) transmitter (TX) failure has occurred. Reduced CPU some cores may be disabled.          Critical
      L-8003-   ultrapath.tx_ue     The system will panic and reset. The processor will not be disabled.
      TS

166   SPINTE    fault.cpu.intel.    A processor has detected an unknown uncorrectable error. Reduced CPU some cores may be disabled.                         Critical
      L-8003-   unknown_ue
      XH

167   SPINTE    fault.cpu.intel.    The Power Control Unit (PCU) on a processor has detected a voltage regulator failure. Reduced CPU some cores             Critical
      L-8003-   vr_failure          may be disabled. The system is unable to be powered on.
      YD

168   SPINTE    fault.cpu.x86.      A bus interconnect error has been detected. Reduced CPU some cores may be disabled. The system will panic               Critical
      L-8004-   bus_interconnect    and reset.
      02

169   SPINTE    fault.cpu.x86.      A bus interconnect error has been detected. Reduced CPU some cores may be disabled. The system will panic               Critical
      L-8004-   bus_timeout         and reset.
      1X

170   SPINTE    fault.cpu.x86.      A processor has detected a cache uncorrectable error. Reduced CPU some cores may be disabled. The system                Critical
      L-8004-   cache_ue            will most likely panic and reset although it is possible under certain conditions that the system may continue to
      3J                            operate in the presence of this fault. System performance may be impacted due to disabled core(s).

171   SPINTE    fault.cpu.x86.      A processor has detected a data cache uncorrectable error. Reduced CPU some cores may be disabled. The                  Critical
      L-8004-   dcache_ue           system will most likely panic and reset although it is possible under certain conditions that the system may continue
      5Q                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

172   SPINTE    fault.cpu.x86.      A processor has detected a data TLB uncorrectable error. Reduced CPU some cores may be disabled. The                    Critical
      L-8004-   dtlb_ue             system will most likely panic and reset although it is possible under certain conditions that the system may continue
      7R                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

173   SPINTE    fault.cpu.x86.      A processor has detected an instruction cache uncorrectable error. Reduced CPU some cores may be disabled.              Critical
      L-8004-   icache_ue           The system will most likely panic and reset although it is possible under certain conditions that the system may
      9D                            continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

174   SPINTE    fault.cpu.x86.      A processor has detected an instruction TLB uncorrectable error. Reduced CPU some cores may be disabled. The            Critical
      L-8004-   itlb_ue             system will most likely panic and reset although it is possible under certain conditions that the system may continue
      C3                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

175   SPINTE    fault.cpu.x86.      A processor has detected a level 0 cache uncorrectable error. Reduced CPU some cores may be disabled. The               Critical
      L-8004-   l0cache_ue          system will most likely panic and reset although it is possible under certain conditions that the system may continue
      E5                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

176   SPINTE    fault.cpu.x86.      A processor has detected a level 0 data cache uncorrectable error. Reduced CPU some cores may be disabled.              Critical
      L-8004-   l0dcache_ue         The system will most likely panic and reset although it is possible under certain conditions that the system may
      GA                            continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

177   SPINTE    fault.cpu.x86.      A processor has detected a level 0 data TLB uncorrectable error. Reduced CPU some cores may be disabled. The            Critical
      L-8004-   l0dtlb_ue           system will most likely panic and reset although it is possible under certain conditions that the system may continue
      JE                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

178   SPINTE    fault.cpu.x86.      A processor has detected a level 0 instruction cache uncorrectable error. Reduced CPU some cores may be                  Critical
      L-8004-   l0icache_ue         disabled. The system will most likely panic and reset although it is possible under certain conditions that the system
      L2                            may continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

179   SPINTE    fault.cpu.x86.      A processor has detected a level 0 instruction TLB uncorrectable error. Reduced CPU some cores may be                    Critical
      L-8004-   l0itlb_ue           disabled. The system will most likely panic and reset although it is possible under certain conditions that the system
      N4                            may continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

180   SPINTE    fault.cpu.x86.      A processor has detected a level 0 TLB uncorrectable error. Reduced CPU some cores may be disabled. The                 Critical
      L-8004-   l0tlb_ue            system will most likely panic and reset although it is possible under certain conditions that the system may continue
      QC                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

181   SPINTE    fault.cpu.x86.      A processor has detected a level 1 data cache uncorrectable error. Reduced CPU some cores may be disabled.                Critical
      L-8004-   l1dcache_ue         The system will most likely panic and reset although it is possible under certain conditions that the system may
      UH                            continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

182   SPINTE    fault.cpu.x86.      A processor has detected a level 1 cache uncorrectable error. Reduced CPU some cores may be disabled. The                 Critical
      L-8004-   l1cache_ue          system will most likely panic and reset although it is possible under certain conditions that the system may continue
      SY                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

183   SPINTE    fault.cpu.x86.      A processor has detected a level 1 data TLB uncorrectable error. Reduced CPU some cores may be disabled. The              Critical
      L-8004-   l1dtlb_ue           system will most likely panic and reset although it is possible under certain conditions that the system may continue
      WP                            to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

184   SPINTE    fault.cpu.x86.      A processor has detected a level 1 instruction cache uncorrectable error. Reduced CPU some cores may be                   Critical
      L-8004-   l1icache_ue         disabled. The system will most likely panic and reset although it is possible under certain conditions that the system
      YS                            may continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

185   SPINTE    fault.cpu.x86.      A processor has detected a level 1 instruction TLB uncorrectable error. Reduced CPU some cores may be disabled.           Critical
      L-8005-   l1itlb_ue           The system will most likely panic and reset although it is possible under certain conditions that the system may
      1S                            continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).
186   SPINTE    fault.cpu.x86.            A processor has detected a level 1 TLB uncorrectable error. Reduced CPU some cores may be disabled. The                  Critical
      L-8005-   l1tlb_ue                  system will most likely panic and reset although it is possible under certain conditions that the system may continue
      3P                                  to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

187   SPINTE    fault.cpu.x86.            A processor has detected a level 2 cache uncorrectable error. Reduced CPU some cores may be disabled. The                Critical
      L-8005-   l2cache_ue                system will most likely panic and reset although it is possible under certain conditions that the system may continue
      5H                                  to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

188   SPINTE    fault.cpu.x86.            A processor has detected a level 2 data cache uncorrectable error. Reduced CPU some cores may be disabled.               Critical
      L-8005-   l2dcache_ue               The system will most likely panic and reset although it is possible under certain conditions that the system may
      7Y                                  continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

189   SPINTE    fault.cpu.x86.            A processor has detected a level 2 data TLB uncorrectable error. Reduced CPU some cores may be disabled. The             Critical
      L-8005-   l2dtlb_ue                 system will most likely panic and reset although it is possible under certain conditions that the system may continue
      9C                                  to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

190   SPINTE    fault.cpu.x86.            A processor has detected a level 2 instruction TLB uncorrectable error. Reduced CPU some cores may be disabled.          Critical
      L-8005-   l2icache_ue               The system will most likely panic and reset although it is possible under certain conditions that the system may
      C4                                  continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

191   SPINTE    fault.cpu.x86.            A processor has detected a level 2 instruction TLB uncorrectable error. Reduced CPU some cores may be disabled.          Critical
      L-8005-   l2itlb_ue                 The system will most likely panic and reset although it is possible under certain conditions that the system may
      E2                                  continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

192   SPINTE    fault.cpu.x86.            A processor has detected a level 2 TLB uncorrectable error. Reduced CPU some cores may be disabled. The                  Critical
      L-8005-   l2tlb_ue                  system will most likely panic and reset although it is possible under certain conditions that the system may continue
      GE                                  to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

193   SPINTE    fault.cpu.x86.            A processor has detected a Last-Level Cache (LLC) uncorrectable error. Reduced CPU some cores may be                     Critical
      L-8005-   llc_ue                    disabled. The system will most likely panic and reset although it is possible under certain conditions that the system
      JA                                  may continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).

194   SPINTE    fault.cpu.x86.            Excessive temperature has been detected on a system component. Configuration Issue after Repair The system is            Critical
      L-8005-   thermtrip                 powered down immediately.
      KS

195   SPINTE    fault.cpu.x86.            CPU Timeout Failures Reduced CPU some cores may be disabled. The system may panic and reset.                             Critical
      L-8005-   timeout
      L5

196   SPINTE    fault.cpu.x86.            A processor has detected a TLB uncorrectable error. Reduced CPU some cores may be disabled. The system will              Critical
      L-8005-   tlb_ue                    most likely panic and reset although it is possible under certain conditions that the system may continue to operate
      N3                                  in the presence of this fault. System performance may be impacted due to disabled core(s).

197   SPINTE    fault.io.intel.iio.irp-   An integrated I-O fatal coherent interface protocol error has been detected Reduced CPU some cores may be                Critical
      L-8005-   fatal                     disabled. The server will reset however the affected processor is not disabled to allow the host OS to boot up and
      QD                                  operate in the presence of a faulty processor.

198   SPINTE    fault.io.intel.tc.        ILOM has detected that the traffic controller on the Integrated I/O (IIO) of a processor has encountered an              Critical
      L-8005-   uncorrectable             uncorrectable error. Reduced CPU some cores may be disabled. The system will panic and reset.
      VE

199   SPINTE    fault.io.pcie.data-       ILOM has detected that a PCIE link layer is inactive. Reduced Storage OR Network Performance The system may              Critical
      L-8005-   link-layer-inactive       be unable to boot.
      WJ

200   SPINTE    fault.io.pcie.            Indicates that a PCIe component or device has encountered a completer abort error. The host will reset The system        Critical
      L-8008-   device-completer-         will panic and reset.
      DW        abort

201   SPINTE    fault.io.pcie.            The PCIe subsystem has encountered a completion timeout. The host will reset The system will panic and reset.            Critical
      L-8008-   device-
      E1        completion-
                timeout

202   SPINTE    fault.io.pcie.            A PCIe device or processor has encountered a protocol error. The host will reset The system will panic and reset.        Critical
      L-8008-   device-protocol-
      GF        error

203   SPINTE    fault.io.pcie.            A PCIe device or processor has encountered malformed Transaction Layer Packets (TLP). The host will reset The            Critical
      L-8008-   device-received-          system will panic and reset.
      J9        malformed

204   SPINTE    fault.io.pcie.            A PCIe device or processor has received an unsupported request. The host will reset The system will panic and            Critical
      L-8008-   device-received-          reset.
      KT        unsupported-
                request

205   SPINTE    fault.io.pcie.            The PCIe data link layer between a PCIe card and processor has encountered a surprise link down. The host will           Critical
      L-8008-   device-surprise-          reset The system will panic and reset.
      L6        link-down

206   SPINTE    fault.io.pcie.fatal       An integrated I-O fatal error in a downstream PCIE device has been detected. The host will reset The server will         Critical
      L-8005-                             reset however the affected processor is not disabled to allow the host OS to boot up and operate in the presence of
      YX                                  a faulty processor.

207   SPINTE    fault.io.pcie.flow-       A PCIe flow control protocol error between a PCIe device and processor has occurred. The host will reset The             Critical
      L-8008-   control-protocol-         system will panic and reset.
      MV        error
208   SPINTE    fault.io.pcie.link-    A PCIe data link layer has failed. The host will reset The system will panic and reset.                            Critical
      L-8008-   failure
      PL

209   SPINTE    fault.io.pcie.rciep.   Processor RCIEP Uncorrectable The host will reset The system will panic and reset. Replace the faulty processor    Critical
      L-8009-   uncorrectable          at the earliest possible convenience.
      Q8

210   SPINTE    fault.io.pcie.rppio-   A Root Port Processor IO (RPPIO) completion timeout was encountered from a downstream PCIe device. The host        Critical
      L-8008-   completion-            will reset The server will panic and reset.
      SU        timeout

211   SPINTE    fault.io.pcie.rppio-   A Root Port of the Processor IO (RPPIO) memory or IO space encountered a completer abort. The host will reset      Critical
      L-8008-   memio-completer-       The server will panic and reset.
      T8        abort

212   SPINTE    fault.io.pcie.rppio-   A Root Port of the Processor IO (RPPIO) memory or IO space encountered an unsupported request. The host will       Critical
      L-8008-   memio-                 reset The server will panic and reset.
      UM        unsupported-
                request

213   SPINTE    fault.memory.intel.    A memory uncorrectable ECC error on a channel that has a 3D Xpoint DIMM has been detected by the processor.        Critical
      L-8006-   3dx.dimm_link_ue       Reduced Memory some dimms may be disabled The system may panic and reset. System performance may be
      3Y                               impacted due to disabled Memory DIMM modules.

214   SPINTE    fault.memory.intel.    A 3D Xpoint (3DX) DIMM communications failure has occurred due to a protocol error. Reduced Memory some            Critical
      L-8006-   3dx.                   dimms may be disabled The system will be powered off immediately following the overtemperature event. Data
      45        dimm_overtemp          integrity may have been compromised.

215   SPINTE    fault.memory.intel.    ILOM has determined a memory uncorrectable ECC error has been detected by the processor on a Data Center           Critical
      L-8009-   3dx.dimm_ue            Persistent Memory Module (DCPMM), aka 3D Xpoint DIMM. Reduced Memory some dimms may be disabled The
      7U                               system may panic and reset memory channel will be disabled

216   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has detected the system is unable to read or write DIMM voltage information.       Critical
      L-8006-   dimm.vdd-access-       Reduced Memory some dimms may be disabled The system is unable to be powered on.
      LD        failed

217   SPINTE    fault.memory.intel.    An uncorrectable Memory DIMM address/command parity error has been detected. Reduced Memory some dimms             Critical
      L-8006-   dimm_addr_cmd_         may be disabled The system will panic and reset. System performance may be impacted because all Memory
      AJ        parity_ue              DIMMs on the channel are disabled upon next system reboot.

218   SPINTE    fault.memory.intel.    A memory uncorrectable ECC error on a Memory DIMM has been detected. Reduced Memory some dimms may be              Critical
      L-8006-   dimm_ue                disabled The system may panic and reset. System performance may be impacted due to disabled Memory DIMM
      KH                               modules.

219   SPINTE    fault.memory.intel.    MRC Polling Timeout The Host will not boot The system is unable to boot.                                           Critical
      L-8009-   mrc.channel-
      R0        testing-polling-
                timeout

220   SPINTE    fault.memory.intel.    The Coherent Memory Interface (CMI) has encountered a failure during initialization of a memory channel. Reduced   Critical
      L-8008-   mrc.cmi-               CPU some cores may be disabled. The system is unable to boot.
      VF        memchannel-init-
                failed

221   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has detected the system was unable to read the memory controller frequency.        Critical
      L-8007-   mrc.mc-freq-read       Unable to Power On The system is unable to be powered on.
      24

222   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has detected that the Power Controller Unit (PCU) is not responding. Unable        Critical
      L-8007-   mrc.pcu-not-           to Power On The system is unable to be powered on.
      5X        responding

223   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has detected a memory controller frequency that is unsupported. Unable to          Critical
      L-8007-   mrc.unsupported-       Power On The system is unable to be powered on.
      6E        mc-freq

224   SPENV-    fault.sp.failed        The service processor is unable to provide platform services to the operating system. No immediate impact to the   Major
      8000-                            host Fault is for informational purposes and does not affect the status of the host OS.
      PG

225   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has detected that a DIMM failed memtest due to multiple symbols. Reduced           Major
      L-8007-   mrc.memtest-           Memory some dimms may be disabled The system is able to boot however system performance may be impacted
      3R        failed-multiple-       as all DIMMs on this channel are not available for use.
                symbol

226   SPINTE    fault.memory.intel.    The Memory Reference Code (MRC) has encountered a memory test failure on a memory channel. Reduced                 Major
      L-8009-   mrc.memory_ch.         Memory some dimms may be disabled The system is able to boot however system performance may be impacted
      1W        boot-check-            as all memory DIMMs in the affected channel are unavailable for use.
                health-mapout

227   SPINTE    fault.memory.intel.    DIMM Zero Margin Error Reduced Memory some dimms may be disabled The system is able to boot however                Major
      L-8009-   mrc.dimm.zero-         system performance may be impacted as the affected DIMM is unavailable for use. Replace the faulty DIMM at the
      UL        margin-error           earliest possible convenience.

228   SPINTE    fault.memory.intel.    SPD Block Unlocked Reduced Memory some dimms may be disabled The system is able to boot however system             Major
      L-8009-   mrc.dimm.spd-          performance may be impacted as all memory DIMMs in the affected channel are unavailable for use.
      TG        block-unlocked
229   SPINTE    fault.memory.intel.   DIMM Power Failure Reduced Memory some dimms may be disabled The system is able to boot however system                Major
      L-8009-   mrc.dimm.power-       performance may be impacted as the affected DIMM is unavailable for use. Replace the faulty DIMM at the earliest
      SV        failure               possible convenience.

230   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has encountered a memory test failure on a memory DIMM. Reduced Memory                Major
      L-8009-   mrc.dimm.boot-        some dimms may be disabled The system will continue to operate in the presence of this fault. System performance
      01        check-health-         may be impacted because not all memory may be available.
                failure

231   SPINTE    fault.memory.intel.   A 3D Xpoint (3DX) DIMM has encountered an SMBUS write error. Reduced Memory some dimms may be disabled                Major
      L-8006-   mrc.dimm.3dx.         The system is able to boot however system performance may be impacted as all memory DIMMs in the affected
      XC        smbus-write-error     channel are unavailable for use.

232   SPINTE    fault.memory.intel.   The Memory Reference Code has detected a SMBUS read error on a DCPMM DIMM. Reduced Memory some                        Major
      L-8008-   mrc.dimm.3dx.         dimms may be disabled The system is able to boot however system performance may be impacted as all memory
      YW        smbus-read-error      DIMMs in the affected channel are unavailable for use.

233   SPINTE    fault.memory.intel.   The Address Indirection Table (AIT) for a DCPMM DIMM is not ready. Reduced Memory some dimms may be                   Major
      L-8009-   mrc.dimm.3dx.ait-     disabled The system is able to boot performance may be impacted as the DCPMM is unavailable.
      9G        dram-notready

234   SPINTE    fault.memory.intel.   A memory channel failure has occurred. Reduced Memory some dimms may be disabled The system is able to                Major
      L-8006-   memory_ch_fail        boot however system performance may be impacted as all memory DIMMs in the affected channel are unavailable
      PS                              for use.

235   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) detected a timing margin error during DIMM training. The host will reset The          Major
      L-8009-   memory_ch.            system is able to boot, however system performance may be impacted as all memory DIMMs in the affected
      V9        training-timing-      channel are unavailable for use.
                margin

236   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected a memory channel training failure. Reduced Memory some                   Major
      L-8006-   memory_ch.            dimms may be disabled The system is able to boot however system performance may be impacted as all DIMMs on
      WR        training-failed       this channel are not available for use.

237   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected an uncorrectable swizzle discovery error on a memory channel.            Major
      L-8006-   memory_ch.            Reduced Memory some dimms may be disabled The system is able to boot however system performance may be
      V4        swizzle-disc-         impacted as all DIMMs on this channel are not available for use.
                uncorrectable

238   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected that a memory channel on-die termination (ODT) timing overflow           Major
      L-8006-   memory_ch.odt-        has occurred. Reduced Memory some dimms may be disabled The system is able to boot however system
      SJ        timing-overflow       performance may be impacted as all DIMMs on this channel are not available for use.

239   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected a DIMM has failed training. Reduced Memory some dimms may                Major
      L-8006-   memory_ch.flyby-      be disabled The system is able to boot however system performance may be impacted as all DIMMs on this
      Q5        uncorrectable         channel are not available for use.

240   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected a clock (CLK) training error. Reduced Memory some dimms may              Major
      L-8006-   memory_ch.cmd-        be disabled The system is able to boot however system performance may be impacted as all DIMMs on this
      NA        clk-training          channel are not available for use.

241   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected a CLK loopback training error. Reduced Memory some dimms                 Major
      L-8006-   memory_ch.clk-        may be disabled The system is able to boot however system performance may be impacted as all DIMMs on this
      MP        loopback-training     channel are not available for use.

242   SPINTE    fault.memory.intel.   The Memory Reference Code (MRC) has detected a memory DIMM that has failed receive-enable training.                   Major
      L-8006-   dimm.receive-         Reduced Memory some dimms may be disabled The system is able to boot however system performance may be
      J3        enable-training       impacted as the affected memory DIMM and all other DIMMs on its memory channel are not available for use.

243   SPINTE    fault.memory.intel.   A memory channel failure has occurred. Reduced Memory some dimms may be disabled The system is able to boot           Major
      L-8006-   dimm.3dx.health-      however system performance may be impacted as the affected memory DIMM is not available for use.
      8X        fatal

244   SPINTE    fault.memory.intel.   The health status of a Data Center Persistent Memory Module (DCPMM) aka 3D Xpoint (3DX) DIMM is failing.              Major
      L-8006-   dimm.3dx.health-      Reduced Memory some dimms may be disabled The affected memory DIMM is still in use and the system will
      7P        failing               continue to operate but could fail at any time.

245   SPINTE    fault.memory.intel.   A DIMM has encountered an excessive number of memory correctable errors. Reduced Memory some dimms may                Major
      L-8006-   dimm.3dx.fatal        be disabled The system is able to boot however system performance may be impacted as the affected memory
      6A                              DIMM is not available for use.

246   SPINTE    fault.memory.intel.   The ILOM fault manager has received an error report indicating the Memory Reference Code (MRC) has                    Major
      L-8006-   3dx.                  determined a 3D Xpoint (3DX) DIMM encountered a fatal error. Reduced Memory some dimms may be disabled
      5S        dimm_protocol_ue      The system is able to boot however system performance may be impacted as the affected memory DIMM is
                                      unavailable for use.

247   SPINTE    fault.io.pcie.        A PCIe device encountered an Access Control Services (ACS) violation error. The host will reset The server will       Major
      L-8008-   device-received-      panic and reset.
      HN        acs-violation

248   SPINTE    fault.io.intel.iio.   An integrated I-O fatal vtd error has been detected. Reduced CPU some cores may be disabled. The server will          Major
      L-8005-   vtd-fatal             reset however the affected processor is not disabled to allow the host OS to boot up and operate in the presence of
      TC                              a faulty processor.

249   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected that the Video Graphics Array (VGA) range              Major
      L-8003-   ultrapath.vga-        target has an invalid stack. Reduced CPU some cores may be disabled. The system is able to boot however
      W3        stack-missing         system performance may be impacted as the UPI link speed may not operate at normal levels.
250   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected that the Video Graphics Array (VGA) range                Major
      L-8003-   ultrapath.vga-soc-    target has an invalid socket. Reduced CPU some cores may be disabled. The system is able to boot however
      VY        missing               system performance may be impacted as the UPI link speed may not operate at normal levels.

251   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected that the requested Ultrapath link speed is               Major
      L-8003-   ultrapath.            unsupported. Reduced CPU some cores may be disabled. The system is able to boot however system
      U5        unsupported-          performance may be impacted.
                speed

252   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected that the processors do not support Time Stamp            Major
      L-8003-   ultrapath.tsc-sync-   Counter (TSC) synchronization. Reduced CPU some cores may be disabled. The system is able to boot however
      SA        unsupported           system performance may be impacted as the UPI link speed may not operate at normal levels.

253   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected an Ultrapath Interconnect (UPI) resource request         Major
      L-8003-   ultrapath.            that was too large for the processor. Reduced CPU some cores may be disabled. The system is able to boot
      KC        resource-not-met      however system performance may be impacted as the UPI link speed may not operate at normal levels.

254   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected an Ultrapath Interconnect (UPI) resource for the         Major
      L-8003-   ultrapath.            processor that was not requested. Reduced CPU some cores may be disabled. The system is able to boot
      LQ        resource-not-         however system performance may be impacted.
                requested

255   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect Reference Code (UPIRC) has detected mismatched Ultrapath Interconnect (UPI) link             Major
      L-8003-   ultrapath.option-     ends. Reduced CPU some cores may be disabled. The system is able to boot however system performance may
      GY        mismatch              be impacted as the UPI link speed may not operate at normal levels.

256   SPINTE    fault.cpu.intel.      The Ultrapath Interconnect (UPI) has detected that a link has degraded width. Reduced CPU some cores may be            Major
      L-8003-   ultrapath.            disabled. The system is able to boot however system performance may be impacted as less than half the lanes are
      F3        link_width_degrad     available.
                ed

257   SPENV-    fault.chassis.        chassis power-off/power-on button is either obstructed or has malfunctioned . Reduced power or cooling to the           Major
      8000-     device.power-         Server. The system will not be able to power on.
      WF        button-malfunction

258   SPINTE    defect.memory.        An unknown error code from the Memory Reference Code has been detected and has not been registered with the             Major
      L-8002-   intel.mrc.            ILOM fault diagnosis daemon. Reprovision Required. Indeterminate. The system may or may not be able to boot
      9X        unknown-errcode       but this largely depends on the nature of the error.

259   SPINTE    defect.memory.        An unexpected error code from the Memory Reference Code has been detected and is not clearly defined in the             Major
      L-8002-   intel.mrc.            BIOS. Reprovision Required. Indeterminate. The system may or may not be able to boot but this largely depends
      82        unexpected-           on the nature of the error.
                errcode

260   SPINTE    defect.memory.        Row Failures List Not Updated. Reprovision Required. The system is able to boot however system performance              Major
      L-8009-   intel.mrc.row-        may be impacted as the MRC will have to use default values for the temperature thresholds. Upgrade to the latest
      L1        failures-list-        ILOM/BIOS Firmware.
                update-failed

261   SPINTE    defect.memory.        The Memory Reference Code (MRC) is unable to support patrol scrub operations. No immediate impact to the host.         Major
      L-8008-   intel.mrc.patrol-     The system will continue to operate in the presence of this defect. The memory patrol scrubber will not be available.
      06        scrub-disabled

262   SPINTE    defect.memory.        An error in the Memory Reference Code (MRC) has been detected. Unable to Power On. The system is unable to             Major
      L-8002-   intel.mrc.internal    be powered on.
      33

263   SPINTE    defect.memory.        The Memory Reference Code (MRC) has determined that the power management thermal table for DIMMs was not                Major
      L-8007-   intel.mrc.dimm.       found. No immediate impact to the host. The system will continue to operate in the presence of this alert. System
      US        power-mgt-            performance may be impacted due to suboptimal thermal throttling of DIMMs.
                thermal-table-not-
                found

264   SPINTE    defect.memory.        Power Management Temp Threshold Invalid. Reprovision Required. The system is able to boot however system                Major
      L-8009-   intel.mrc.dimm.       performance may be impacted as the MRC will have to use default values for the temperature thresholds. Upgrade
      KW        power-mgt-            to the latest ILOM/BIOS Firmware.
                temperature-
                threshold-invalid

265   SPINTE    defect.memory.        The Memory Reference Code (MRC) has determined that an internal opcode is either invalid or not defined.               Major
      L-8002-   intel.mrc.dimm.       Reduced Memory some dimms may be disabled. The system is able to boot however system performance may be
      1D        invalid-fnv-opcode    impacted as all DIMMs on this channel are not available for use.

266   SPINTE    defect.memory.        the Memory Reference Code detected a non-serviceable surprise clock stop on a 3D Xpoint (3DX) DIMM.                    Major
      L-8002-   intel.mrc.dimm.       Reprovision Required. The system is power-cycled.
      0H        3dx.surprise-
                clock-error-
                nonserviceable

267   SPINTE    defect.memory.        The Memory Reference Code (MRC) detected a surprise clock stop error on a 3D Xpoint (3DX) DIMM that was not             Major
      L-8001-   intel.mrc.dimm.       resolved by a power cycle. Reduced Memory some dimms may be disabled. The system is able to boot however
      Y2        3dx.surprise-         system performance may be impacted as the affected memory DIMM is unavailable for use.
                clock-error

268   SPINTE    defect.memory.        The Memory Reference Code (MRC) does not recognize the interface used to access 3DX registers. Reduced                 Major
      L-8001-   intel.mrc.dimm.       Memory some dimms may be disabled. The system is able to boot however system performance may be impacted.
      XX        3dx.invalid-
                access-mode
269   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected an invalid opcode for memory DIMM. No immediate impact to             Major
      L-8001-   intel.dimm.invalid-   the host. None.
      S4        fnv-opcode

270   SPINTE    defect.memory.        The Memory Reference Code (MRC) has detected a failure with setting up memory interleaving. No immediate           Major
      L-8007-   intel.dimm.           impact to the host. The system will continue to operate in the presence of this alert. System performance may be
      T5        interleave-failure    impacted because not all memory may be available.

271   ILOM-     defect.ilom.boot.     The preferred ILOM firmware image could not be booted. Reprovision Required. The ILOM backup image is likely       Major
      8000-6N   preferred-invalid     to be an older and possibly out of date image.

272   SPINTE    defect.cpu.intel.     An unknown error code from the Ultrapath Interconnect (UPI) Reference Code has been detected and has not been       Major
      L-8001-   ultrapath.            registered with the ILOM fault diagnosis daemon. Reprovision Required. Indeterminate. The system may or may
      PD        unknown-errcode       not be able to boot but this largely depends on the nature of the error.

273   SPINTE    defect.cpu.intel.     An unexpected error code from the Ultrapath Interconnect (UPI) Reference Code has been detected and is not          Major
      L-8001-   ultrapath.            clearly defined in the BIOS. Reprovision Required. Indeterminate. The system may or may not be able to boot but
      NY        unexpected-           this largely depends on the nature of the error.
                errcode

274   SPINTE    defect.cpu.intel.     Ultrapath Config Unknown. Reprovision Required. The system may be able to boot however system performance           Major
      L-8009-   ultrapath.platform-   may be impacted
      HK        config-unknown
                                      as the MRC will have to use default values for some internal parameters.

                                      Some memory channels may get disabled.

275   SPINTE    defect.cpu.intel.     The Ultrapath Interconnect (UPI) initialization code has detected a slow UPI link. Reduced CPU some cores may      Major
      L-8001-   ultrapath.link-slow   be disabled. The system is able to boot however system performance will be severely impacted.
      JP

276   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has determined that the Total Memory Encryption (TME) physical address bits         Major
      L-8007-   mrc.tme-physical-     have exceeded maximum value. Reduced Memory some dimms may be disabled. The system will continue to
      Q2        address-bits-over-    operate in the presence of this alert. Multi-Key Total Memory Encryption (MKTME) will be unavailable.
                max

277   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has determined that a combination of DIMM types across sockets associated           Major
      L-8007-   mrc.socket-dimm-      with a processor is invalid. Reduced Memory some dimms may be disabled. The system will continue to operate in
      PX        type-combination-     the presence of this alert. System performance may be impacted because some DIMMs will be configured out.
                invalid

278   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has encountered an invalid DIMM configuration using memory population               Major
      L-8007-   mrc.socket-dimm-      rules and guidelines for a processor socket. Reduced Memory some dimms may be disabled. The system will
      NE        population-rules-     continue to operate in the presence of this alert. System performance may be impacted because some DIMMs will
                mapout                be configured out. Other alerts or faults will indicate the specific dimms that are configured out.

279   SPINTE    alert.memory.intel.   DIMM Socket Configuration is Nonuniform. The Host will not boot. ILOM has determined that the Memory                Major
      L-8009-   mrc.socket-dimm-      Reference Code (MRC) detected the DIMM configuration is not uniform across all sockets.
      X6        config-nonuniform

280   SPINTE    alert.memory.intel.   Mem Channel Mixed Widths Unsupported. Configuration Issue after Repair. The system is able to boot however          Major
      L-8009-   mrc.memory_ch.        system performance may be impacted as all memory DIMMs in the affected channel are unavailable for use.
      FN        mixed-widths-
                unsupported

281   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected a 3DX DIMM that is not recognized due to some mismatch with            Major
      L-8001-   mrc.dimm.3dx.         current configuration data in the DIMM firmware. Reduced Memory some dimms may be disabled. The affected
      2P        firmware-             memory DIMM is not available for use. The system is able to boot however system performance may be impacted.
                unsupported

282   SPINTE    alert.memory.intel.   The geometry of a DDR4 Memory DIMM is not supported. Reduced Memory some dimms may be disabled. The                Major
      L-8001-   mrc.dimm.ddr-         affected memory DIMM is not available for use. The system is able to boot however system performance may be
      3A        geometry-             impacted.
                unsupported

283   SPINTE    alert.memory.intel.   LRDIMM Unsupported. Configuration Issue after Repair. The system is able to boot however system performance         Major
      L-8009-   mrc.dimm.lrdimm-      may be impacted as all memory DIMMs in the affected channel are unavailable for use. Remove the LRDIMM from
      E6        unsupported           the system.

284   SPINTE    alert.memory.intel.   DIMM Vendor Version Unsupported. The Host will not boot. ILOM has determined the Memory Reference Code              Major
      L-8009-   mrc.dimm.vendor-      (MRC) detected the DIMM vendor version is unsupported.
      WN        version-
                unsupported

285   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected memory DIMMs on a memory channel with different Stock-                 Major
      L-8000-   dimm.ngn-sku-         Keeping-Unit (SKU) numbers. Reduced Memory some dimms may be disabled. The system will be unable to boot
      M4        mismatch              and no video output to the Host console. A fatal error will result in the entire memory subsystem to be unusable.

286   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected an unsupported non-production memory DIMM. Reduced                    Major
      L-8000-   dimm.nonprod-         Memory some dimms may be disabled. The system is able to boot however system performance may be impacted
      NR        unsupported           as all memory DIMMs in the affected channel are unavailable for use.

287   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected an unsupported number of ranks on a memory DIMM. Reduced              Major
      L-8000-   dimm.num-ranks-       Memory some dimms may be disabled. The system is able to boot however system performance may be impacted
      PC        unsupported           as all memory DIMMs in the affected channel are unavailable for use.

288   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected a registered DIMM (RDIMM) on a board that only supports                Major
      L-8000-   dimm.rdimm-           unbuffered/unregistered memory DIMMs (UDIMM). Reduced Memory some dimms may be disabled. The system is
      QQ        unsupported           able to boot however system performance may be impacted as all memory DIMMs in the affected channel are
                                      unavailable for use.
289   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected a memory DIMM with an unsupported Stock-Keeping-Unit (SKU)                   Major
      L-8000-   dimm.sku-             number. Reduced Memory some dimms may be disabled. The system is able to boot however system performance
      RY        unsupported           may be impacted as all memory DIMMs in the affected channel are unavailable for use.

290   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected an unbuffered/unregistered DIMM (UDIMM) has been installed                   Major
      L-8000-   dimm.udimm-           and is unsupported. Reduced Memory some dimms may be disabled. The system is able to boot however system
      S3        unsupported           performance may be impacted as all memory DIMMs in the affected channel are unavailable for use.

291   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected the memory configuration on a memory channel uses an                         Major
      L-8000-   memory_ch.            unsupported frequency. Configuration Issue after Repair. The system is able to boot however system performance
      TH        frequency-            may be impacted as all memory DIMMs in the affected channel are unavailable for use.
                unsupported

292   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected the number of ranks on a memory channel is unsupported.                     Major
      L-8000-   memory_ch.            Configuration Issue after Repair. The system is able to boot however system performance may be impacted as all
      UD        numranks-             memory DIMMs in the affected channel are unavailable for use.
                unsupported

293   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has detected memory DIMMs on a memory channel in violation of the memory                  Major
      L-8000-   memory_ch.            DIMM population rules. Reduced Memory some dimms may be disabled. The system is able to boot however
      VP        population-invalid    system performance may be impacted as all memory DIMMs in the affected channel are unavailable for use.

294   SPINTE    alert.memory.intel.   The memory configuration does not support two-level main memory (2LM) mode. Reduced Memory some dimms                    Major
      L-8000-   mrc.2lm-mc-           may be disabled. The system is able to boot however system performance may be impacted.
      WA        memory-mismatch

295   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has determined that the number of far memory channels is not a power of 2 in              Major
      L-8007-   mrc.2lm-num-fm-       2LM mode. Reduced Memory some dimms may be disabled. The system will continue to operate in the presence
      FY        ch-notpwr2            of this alert. System performance may be impacted because the memory mode will be switched from 2LM to 1LM.

296   SPINTE    alert.memory.intel.   The Memory Reference Code (MRC) has determined that the Data Center Persistent Memory Modules (DCPMM)                     Major
      L-8007-   mrc.3dx.sgx-          cannot be used in Persistent Memory Mode when Software Guard Extensions (SGX) are enabled. Reduced
      G3        persistent-           Memory some dimms may be disabled. The system will continue to operate in the presence of this alert. Persistent
                memory-disabled       memory will not be available.

297   SPINTE    alert.memory.intel.   The Data Center Persistent Memory Modules (DCPMM) cannot be used in Persistent Memory Mode when Total                     Major
      L-8007-   mrc.3dx.tme-          Memory Encryption (TME) is enabled. Reduced Memory some dimms may be disabled. The system will continue to
      J4        persistent-           operate in the presence of this alert. Persistent memory will not be available.
                memory-disabled

298   SPENV-    alert.chassis.        Power Supply Missing. Configuration Issue after Repair. Loss of redundant power.                                          Major
      8001-3F   config.psu.missing

299   SPENV-    alert.chassis.        NIC is missing. Unable to Power On. System will not power on.                                                            Major
      8002-86   config.nic.missing

300   SPGX-     fault.gpu.mem.        GPU Row Remapping Exceed Threshold. The host will reset. Failure to offline the GPU may cause the server to fail          Major
      8000-K3   row-remapping-        due to fatal memory errors. Replace the GPU at the earliest possible convenience.
                failed

301   SPGXT     fault.io.pcie.link-   Indicates that a PCI link error has occurred on a sled of the G4-8c. Reduced Storage OR Network Performance.              Major
      AIL-      degraded-width        System will continue to operate however performance may be impacted.
      8000-R0

302   ISTOR-    alert.io.disk.life-   The SMART health-monitoring has detected the Percent Drive Life Used (PDLU) on disk device has fallen below               Major
      8000-AR   low                   the "WARNING" threshold set by the manufacturer. Reduced Storage OR Network Performance. The disk is fast
                                      approaching its end of useful life. Continued use of this disk may result in performance degradation or possible loss
                                      of data.

303   ISTOR-    fault.io.disk.life-   The SMART health-monitoring has detected that the Percent Drive Life Used (PDLU) on disk device has fallen                Major
      8000-C4   critical              SIGNIFICANTLY below the threshold set by the manufacturer."" . Reduced Storage OR Network Performance. The
                                      disk has reached its end of life. Continued use of this disk may result in performance degradation. Risk of data loss
                                      or data corruption is imminent or is already occurring.

304   ISTOR-    alert.io.device.      The on-die temperature of the device controller has exceeded the warning limit established by the manufacturer."" .       Major
      8000-E2   temperature-high-     Reduced CPU some cores may be disabled. The system will continue to operate however system performance
                warning               may be impacted. A slow down of the processor clock on device controller should result in cool down of device
                                      controller.

305   ISTOR-    fault.io.disk.read-   SMART health-monitoring firmware has reported that the disk has been placed in read-only mode. Reduced                   Major
      8000-8Q   only                  Storage OR Network Performance. Continued operation of this disk may result in data loss.

306   SPGX-     fault.gpu.mem.        An uncorrectable ECC error has caused an application to fail. The host will reset. The application fails but the host   Major
      8000-FC   ecc-contained         is still running.

307   SPGX-     fault.gpu.mem.        GPU Page Retirement Exceeded. Reduced CPU some cores may be disabled. Failure to offline the GPU may                     Major
      8000-JH   page-retire-failed    cause the server to fail due to fatal memory errors. Replace the GPU at the earliest possible convenience.

308   SPENV-    fault.chassis.        A fan module is rotating too slow. Reduced power or cooling to the Server. Loss of redundant cooling.                     Major
      8000-A7   device.fan.fail

309   SPENV-    fault.chassis.        An internal power supply failure has been detected. Reduced power or cooling to the Server. Loss of redundant             Major
      8000-     device.psu.fail       power.
      CU

310   SPENV-    fault.chassis.        PSU Fan Failure. Reduced power or cooling to the Server. Loss of redundant power. Replace the affected power              Major
      8001-RV   device.psu.fan-fail   supply.
311   SPENV-    fault.chassis.        PSU Output Current Exceeded. Reduced power or cooling to the Server. Loss of redundant power. Replace the                Major
      8001-S0   device.psu.output-    affected power supply.
                current-over

312   SPENV-    fault.chassis.        PSU Output Voltage Exceeded. Reduced power or cooling to the Server. Loss of redundant power. Replace the                Major
      8001-TL   device.psu.output-    affected power supply.
                voltage-over

313   SPENV-    fault.chassis.        PSU Output UnderVoltage. Reduced power or cooling to the Server. Loss of redundant power. Replace the affected           Major
      8001-     device.psu.output-    power supply.
      UG        voltage-under

314   SPENV-    alert.chassis.        The Graphix Extension Retimer (GXR) PCIe card installed is not a supported hardware version. The Host will not           Major
      8002-37   config.iou.invalid-   boot. System will not power on.
                gxr

315   SPENV-    alert.chassis.        The Graphix Extension Retimer (GXR) PCIe cards populated in the system are not compatible. The Host will not             Major
      8002-     config.iou.invalid-   boot. System will not power on.
      4W        mixed-gxr

316   SPENV-    alert.chassis.        There is an insufficent number of Graphix Extension Retimer (GXR) PCIe cards populated. The Host will not boot.          Major
      8002-51   config.iou.           System will not power on.
                insufficient-num-
                gxr

317   SPENV-    alert.chassis.fw.     The FPGA upgrade was not performed due to ROT lock-down being asserted. ILOM Impacted No Impact to the                   Major
      8001-     fpga-upgrade-         Host. The system will continue to operate but the FPGA will not have been upgraded.
      GN        blocked

318   SPENV-    alert.chassis.fw.     An upgrade to the Field Programmable Gate Array (FPGA) was unsuccessful. ILOM Impacted No Impact to the                  Major
      8001-HF   fpga-upgrade-         Host. The system will continue to operate but the FPGA will not have been upgraded. Retry the ILOM/SP update.
                failure

319   SPENV-    alert.chassis.        PCIe Data Cable Missing. Configuration Issue after Repair. The system will not be able to power on.                      Major
      8000-VK   config.iou.pcie-
                cable.missing

320   SPENV-    alert.chassis.        Power Cable Incorrectly Attached to IOU. Configuration Issue after Repair. The system will not be able to power on.      Major
      8000-     config.iou.power-
      XW        cable.invalid

321   SPENV-    alert.chassis.        IOU Unknown. Configuration Issue after Repair. The system will not be able to power on.                                  Major
      8000-U8   config.iou.
                unknown

322   SPENV-    alert.chassis.        PCIe Device Unexpectedly Removed. Configuration Issue after Repair. The system will reboot and the device will           Major
      8001-VN   config.pcie.          no longer be available. Removal of hot-plug devices must be performed properly to prevent unexpected interruption
                missing               of system operation

323   ILOM-     alert.ilom.chassis.   The key identity properties (KIP) of the system are indeterminable. ILOM unable to Initialize Host may not start. The   Major
      8000-H0   tli.invalid           system will operate in the presence of this fault.

                                      The product serial number (PSN) is a key identity property and is required for service entitlement

324   SPENV-    defect.chassis.spi.   The bootstrap code on the SPI flash is unrecognized. Reprovision Required. Occurs during SP initialization.              Major
      8001-ET   firmware.boot-
                image-
                unrecognized

325   SPENV-    defect.chassis.spi.   A SPI flash parameter is not set to factory default. Reprovision Required. Occurs during SP initialization.             Major
      8001-F9   firmware.
                parameter-
                incorrect

326   ILOM-     defect.ilom.fdd.      ILOM has detected that a number of open faults have exceeded threshold limit. ILOM Impacted No Impact to the            Major
      8000-     max_faults            Host. No future events will be diagnosed on the affected FRU until prior issues have been resolved.
      KG

327   ILOM-     defect.ilom.fs.full   ILOM has detected that its file system has exceeded the filesystem capacity limit. ILOM Impacted No Impact to the      Major
      8000-JV                         Host. Files are deleted. ILOM commands may fail especially those which make configuration changes.

328   SPGXT     fault.chassis.gx.     Indicates that a PCIe switch on the IOB has caused a PCIe reset. Reduced CPU, some cores may be disabled. All          Major
      AIL-      pcie.switch-reset-    downstream devices will be unavailable.
      8000-G9   assert

329   ILOM-     fault.fruid.corrupt   indicates that the fault management function running on the service processor has determined a Field Replaceable         Major
      8000-2V                         Unit (FRU) has a corrupt FRUID SEEPROM. Unable to Power On. System may not boot.

330   ILOM-     fault.fruid.          A Field Replaceable Unit (FRU) FRUID SEEPROM cannot be accessed. Reduced Storage OR Network                             Major
      8000-D8   inaccessible          Performance. The system may not be able to use one or more components on the affected FRU. This may prevent
                                      the system from powering on.

331   ISTOR-    fault.io.disk.        SMART health-monitoring firmware has reported that the volatile memory backup device has failed. Reduced                Major
      8000-9C   backup-device-fail    Storage OR Network Performance. Performance degradation is likely and continued operation of this disk may
                                      result in data loss.

332   ISTOR-    fault.io.disk.over-   A Disk Temperature has exceeded its threshold. Reduced Storage OR Network Performance. Performance                      Major
      8000-05   temperature           degradation is likely and continued disk operation beyond the temperature threshold can result in disk damage and
                                      potential data loss.
333   ISTOR-    fault.io.disk.         A Predictive Disk Failure is Imminent. Reduced Storage OR Network Performance. It is likely that the continued       Major
      8000-1S   predictive-failure     operation of this disk will result in data loss.

334   SPENV-    alert.chassis.         PCIe Cable Unsupported . Configuration Issue after Repair. The system will be unable to power on.                     Major
      8001-P8   config.iou.pcie-
                cable.unsupported      Remove PCIe cable from the PCIe port that does not support hot-plug.

335   SPENV-    alert.chassis.         FIM Missing or Improperly Attached. Configuration Issue after Repair. The system will continue to operate in the      Major
      8000-Y1   config.rot.cabling     presence of this alert but functionality may be reduced.

336   SPINTE    alert.chassis.         A power-cycle of the host by ILOM was unsuccessful in resetting the Platform Controller Hub (PCH). Unable to         Major
      L-8000-   domain.intel.pch.      Power On. The system is down. A manual power cycle of the system is required.
      4Q        reset-hung

337   SPINTE    alert.chassis.intel.   The Management Engine is in recovery mode and any warm resets of the host OS will become global resets.              Major
      L-8000-   me-recovery-           Reprovision Required. There is no protection or warning of a global reset occurring when a warm reset was actually
      5C        mode                   expected.

338   SPINTE    alert.chassis.intel.   Multiple Platform Controller Hub (PCH) failures to service a power-on request have occurred. No direct impact look   Major
      L-8000-   pch.unresponsive       for associated events. System is unable to power on.
      74

339   SPENV-    alert.chassis.         PSU Overvoltage Input Exceeded. Configuration Issue after Repair. Connect the power supply to a power                 Major
      8001-     power.ext-             receptacle that provides a supported voltage range.
      QM        overvoltage

340   SPENV-    alert.cpu.x86.         Processor / Memory Throttling. No direct impact look for associated events. System performance degradation may        Major
      8001-M7   prochot-persistent     occur. Check the system for any known fault events related to the fans or cooling of the internal components within
                                       the server.

341   SPENV-    alert.ilom.chassis.    NVME Drive Unsupported. Configuration Issue after Repair. The NVME drive is unusable.                                 Major
      8001-     config.drive.nvme-
      0W        unsupported

342   SPENV-    alert.ilom.chassis.    SAS Drive Unsupported. Configuration Issue after Repair. The SAS drive is unusable.                                   Major
      8001-11   config.drive.sas-
                unsupported

343   SPINTE    alert.io.pcie.link-    PCIe Link Training Failure. No immediate impact to the host. Happens 3 times and then you get the true PCIe fault.    Major
      L-8009-   training-failed-
      YT        nonserviceable

344   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected a DDR4 DIMM that does not support 1.2-Volt. Configuration               Major
      L-8000-   ddr4-1_2v-             Issue after Repair. The system is able to boot however system performance may be impacted as all memory
      A3        unsupported            DIMMs in the affected channel are unavailable for use.

345   SPINTE    alert.memory.intel.    24GB DIMM Unsupported. Configuration Issue after Repair. The system is able to boot however system                    Major
      L-8009-   dimm.24gb-             performance may be impacted as the affected memory DIMM is unavailable for use.
      C0        unsupported

346   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected a DIMM that stacks multiple DRAMS on a DIMM (3DS) is                     Major
      L-8000-   dimm.3ds-              unsupported. Reduced Memory some dimms may be disabled. The system is able to boot however system
      D5        unsupported            performance may be impacted as the affected memory DIMM is unavailable for use.

347   SPINTE    alert.memory.intel.    Unexpected shutdown has occurred and data committed to 3DX DIMM may not have been persisted. No direct                Major
      L-8000-   dimm.3dx.              impact look for associated events. Data stored in the Data Center Persistent Memory Module (DCPMM) a.k.a. 3d
      ES        dirty_shutdown_n       Xpoint (3DX) DIMM may have been lost. The application using the DCPMM DIMM is responsible for ensuring data
                onserviceable          loss does not occur.

348   SPINTE    alert.memory.intel.    A 3D Xpoint (3DX) DIMM is unsupported. Reduced Memory some dimms may be disabled. The affected memory                Major
      L-8000-   dimm.3dx.              DIMM is not available for use. The system is able to boot however system performance may be impacted.
      FA        unsupported

349   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected a set of DIMMs that violates DIMM population rules. Reduced            Major
      L-8000-   dimm.invalid-pop       Memory some dimms may be disabled. The system is able to boot however system performance may be impacted
      HE                               as the affected memory DIMMs may be unavailable for use.

350   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has detected invalid Serial Presence Detect (SPD) contents in a memory                Major
      L-8000-   dimm.invalid-spd-      DIMM. Reduced Memory some dimms may be disabled. The system is able to boot however system performance
      JJ        content                may be impacted as the affected memory DIMMs are unavailable for use.

351   SPINTE    alert.memory.intel.    9x4 DIMM Config Invalid. Configuration Issue after Repair. The system is able to boot however system performance      Major
      L-8009-   mrc.9x4-dimm-          may be impacted as the affected memory DIMM is unavailable for use
      DT        config-invalid

352   SPINTE    alert.memory.intel.    The Memory Reference Code (MRC) has determined that the AppDirect x1 operation is not allowed for the current         Major
      L-8007-   mrc.adx1-              DIMM population configuration. Configuration Issue after Repair. The system will continue to operate in the
      KQ        population-            presence of this alert. AppDirect x1 operation will not be possible.
                mismatch

353   SPINTE    alert.memory.intel.    Memory Reference Code (MRC) has identified DDR4 DIMMs on a processor socket have mismatched capacities.              Major
      L-8009-   mrc.ddr-capacity-      Configuration Issue after Repair. The system will continue to operate in the presence of this alert. System
      AV        mismatch               performance may be impacted because some DIMMs will be configured out. Other alerts or faults will indicate the
                                       specific DIMMs that are configured out.

354   SPENV-    fault.chassis.         12-Volt Failure Predicted. Reduced power or cooling to the Server. The system may shutdown soon.                      Major
      8001-2K   connector.12v.
                failure-predicted
355   SPINTE    fault.io.pcie.         PCIe Device Initialization Failed Reduced Storage OR Network Performance The PCIe device is unusable.                  Major
      L-8005-   device-init-failed
      X2

356   SPINTE    fault.memory.intel.    A memory channel failure has occurred. Reduced Memory some dimms may be disabled The system is able to boot            Major
      L-8006-   dimm.3dx.health-       however system performance may be impacted as the affected memory DIMM is not available for use.
      8X        fatal

357   SPINTE    fault.memory.intel.    A DIMM has encountered an excessive number of memory correctable errors. Reduced Memory some dimms may                 Major
      L-8006-   dimm_excessive_        be disabled The system is able to boot however system performance will be impacted as the affected memory
      EC        ce                     DIMM is unavailable for use.




---

## Other Hardware Faults (ILOM) — Minor and Informational

Columns: **#** | **Fault ID** | **Name** | **Description** | **Severity**

---

1     SPINTE    fault.memory.        Multiple correctable ECC errors on a memory DIMM have been detected. Reduced Memory some dimms may be                    Minor
      L-8006-   intel.dimm_ce        disabled The system will continue to operate in the presence of this fault. The memory DIMM is still in use and is not
      CE                             disabled. If the DIMM_CE_MAP_OUT policy is enabled the memory DIMM is disabled on next system reboot and will
                                     remain unavailable until repaired. System performance may be impacted slightly due to retired memory pages.

2     SPINTE    fault.memory.        Multiple correctable memory DIMM address/command parity errors have been detected. Reduced Memory some                   Minor
      L-8006-   intel.               dimms may be disabled The system will continue to operate in the presence of this fault. System performance may be
      92        dimm_addr_cm         impacted because all Memory DIMMs on the channel are disabled upon next system reboot.
                d_parity_ce

3     SPINTE    fault.memory.        Multiple correctable ECC errors on a channel that has a 3D Xpoint (3DX) DIMM has been detected by the processor.         Minor
      L-8006-   intel.3dx.           Reduced Memory some dimms may be disabled The DIMM will remain in use. The chassis wide processor and
      23        dimm_link_ce         affected memory DIMM's service-required LEDs are illuminated.

4     SPINTE    fault.memory.        Multiple correctable ECC errors have been detected by the processor on a Data Center Persistent Memory Module            Minor
      L-8009-   intel.3dx.           (DCPMM) Reduced Memory some dimms may be disabled System will continue to operate
      67        dimm_ce

5     SPINTE    fault.io.pcie.       Processor RCIEP Correctable No immediate impact to the host The system will continue to operate in the presence of       Minor
      L-8009-   rciep.               this fault. Replace the faulty processor at the earliest possible convenience.
      PM        correctable

6     SPINTE    fault.io.pcie.       An Integrated I/O (IIO) non-fatal error in a PCIe device has been detected. Reduced Storage OR Network Performance       Minor
      L-8008-   nonfatal             System continues to run with degraded resources.
      QG

7     SPINTE    fault.io.pcie.       A PCIe link has encountered excessive CE re-transmissions of a packet due to a bad link. Reduced Storage OR              Minor
      L-8008-   link-excessive-      Network Performance None. The system will continue to operate but may have performance issues it the CE
      N0        ce                   occurrence is high enough.

8     SPINTE    fault.io.pcie.       The ILOM fault manager has applied diagnosis to error reports Reduced Storage OR Network Performance The                 Minor
      L-8006-   link-degraded-       system will continue to operate however system performance may be impacted.
      1H        width

9     SPINTE    fault.io.pcie.       A PCIe device has encountered excessive CE re-transmissions of a packet due to a faulty device. Reduced Storage          Minor
      L-8008-   device-              OR Network Performance None. The system will continue to operate but may have performance issues it the CE
      FK        excessive-ce         occurrence is high enough.

10    SPINTE    fault.io.pcie.       The ILOM fault manager has has determined a PCI link error has occurred which reduces the link speed of a PCI card.      Minor
      L-8006-   link-degraded-       Reduced Storage OR Network Performance The system will continue to operate however system performance may be
      0D        speed                impacted.

11    SPINTE    fault.io.intel.tc.   ILOM has detected that the traffic controller on the Integrated I/O (IIO) of a processor has encountered multiple        Minor
      L-8005-   correctable          correctable errors. Reduced CPU some cores may be disabled. The system will continue to operate in the presence of
      UQ                             this fault.

12    SPINTE    fault.gpu.mem.       GPU Row Remappings Exceed Threshold. The GPU should be manually taken offline immediately. Failure to replace            Minor
      L-800A-   row-remapping-       the GPU may cause the server to encounter fatal memory errors. Reduced CPU, some cores may be disabled. The
      1M        failure              GPU should be manually taken offline immediately. Failure to replace the GPU may cause the server to encounter fatal
                                     memory errors.

13    SPINTE    fault.gpu.mem.       GPU Page Retirement Exceeded Reduced CPU, some cores may be disabled. The GPU should be manually taken                   Minor
      L-800A-   page-retire-         offline immediately. Failure to replace the GPU may cause the server to encounter fatal memory errors.
      08        failure

14    SPINTE    fault.cpu.x86.       A processor has detected multiple TLB correctable errors. Reduced CPU some cores may be disabled. The system             Minor
      L-8005-   tlb_ce               will continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).
      MY

15    SPINTE    fault.cpu.x86.       A processor detected timeout correctable errors that exceed the SERD threshold. Reduced CPU some cores may be            Minor
      L-8009-   timeout_ce           disabled. System will continue to operate
      5M

16    SPINTE    fault.cpu.x86.       A processor has detected multiple Last-Level Cache (LLC) correctable errors. Reduced CPU some cores may be               Minor
      L-8005-   llc_ce               disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
      HP                             to disabled core(s).
17   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 TLB correctable errors. Reduced CPU some cores may be disabled. The            Minor
     L-8005-   l2tlb_ce         system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     FJ                         (s).

18   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 instruction TLB correctable errors. Reduced CPU some cores may be              Minor
     L-8005-   l2itlb_ce        disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     DX                         to disabled core(s).

19   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 instruction cache correctable errors. Reduced CPU some cores may be            Minor
     L-8005-   l2icache_ce      disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     AR                         to disabled core(s).

20   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 data TLB correctable errors. Reduced CPU some cores may be disabled.           Minor
     L-8005-   l2dtlb_ce        The system will continue to operate in the presence of this fault. System performance may be impacted due to
     8Q                         disabled core(s).

21   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 data cache correctable errors. Reduced CPU some cores may be disabled.         Minor
     L-8005-   l2dcache_ce      The system will continue to operate in the presence of this fault. System performance may be impacted due to
     63                         disabled core(s).

22   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 cache correctable errors. Reduced CPU some cores may be disabled. The          Minor
     L-8005-   l2cache_ce       system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     4D                         (s).

23   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 TLB correctable errors. Reduced CPU some cores may be disabled. The            Minor
     L-8005-   l1tlb_ce         system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     2A                         (s).

24   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 instruction TLB correctable errors. Reduced CPU some cores may be              Minor
     L-8005-   l1itlb_ce        disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     05                         to disabled core(s).

25   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 instruction cache correctable errors. Reduced CPU some cores may be            Minor
     L-8004-   l1icache_ce      disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     X5                         to disabled core(s).

26   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 data TLB correctable errors. Reduced CPU some cores may be disabled.           Minor
     L-8004-   l1dtlb_ce        The system will continue to operate in the presence of this fault. System performance may be impacted due to
     VA                         disabled core(s).

27   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 data cache correctable errors. Reduced CPU some cores may be disabled.         Minor
     L-8004-   l1dcache_ce      The system will continue to operate in the presence of this fault. System performance may be impacted due to
     TD                         disabled core(s).

28   SPINTE    fault.cpu.x86.   A processor has detected multiple level 1 cache correctable errors. Reduced CPU some cores may be disabled. The        Minor
     L-8004-   l1cache_ce       system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     R3                         (s).

29   SPINTE    fault.cpu.x86.   A processor has detected multiple level 0 TLB correctable errors. Reduced CPU some cores may be disabled. The          Minor
     L-8004-   l0tlb_ce         system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     PQ                         (s).

30   SPINTE    fault.cpu.x86.   A processor has detected multiple level 0 instruction TLB correctable errors. Reduced CPU some cores may be             Minor
     L-8004-   l0itlb_ce        disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     MR                         to disabled core(s).

31   SPINTE    fault.cpu.x86.   A processor has detected multiple level 0 instruction cache correctable errors. Reduced CPU some cores may be           Minor
     L-8004-   l0icache_ce      disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     KX                         to disabled core(s).

32   SPINTE    fault.cpu.x86.   A processor has detected multiple level 0 data TLB correctable errors. Reduced CPU some cores may be disabled.         Minor
     L-8004-   l0dtlb_ce        The system will continue to operate in the presence of this fault. System performance may be impacted due to
     HJ                         disabled core(s).

33   SPINTE    fault.cpu.x86.   A processor has detected multiple level 2 TLB correctable errors. Reduced CPU some cores may be disabled. The          Minor
     L-8004-   l0dcache_ce      system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     FP                         (s).

34   SPINTE    fault.cpu.x86.   A processor has detected multiple level 0 cache correctable errors. Reduced CPU some cores may be disabled. The        Minor
     L-8004-   l0cache_ce       system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     DS                         (s).

35   SPINTE    fault.cpu.x86.   A processor has detected multiple instruction TLB correctable errors. Reduced CPU some cores may be disabled.          Minor
     L-8004-   itlb_ce          The system will continue to operate in the presence of this fault. System performance may be impacted due to
     AY                         disabled core(s).

36   SPINTE    fault.cpu.x86.   A processor has detected multiple instruction cache correctable errors. Reduced CPU some cores may be disabled.        Minor
     L-8004-   icache_ce        The system will continue to operate in the presence of this fault. System performance may be impacted due to
     8H                         disabled core(s).

37   SPINTE    fault.cpu.x86.   A processor has detected multiple data TLB correctable errors. Reduced CPU some cores may be disabled. The             Minor
     L-8004-   dtlb_ce          system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     64                         (s).

38   SPINTE    fault.cpu.x86.   A processor has detected multiple data cache correctable errors. Reduced CPU some cores may be disabled. The           Minor
     L-8004-   dcache_ce        system will continue to operate in the presence of this fault. System performance may be impacted due to disabled core
     4C                         (s).
39   SPINTE    fault.cpu.x86.      A processor has detected multiple cache correctable errors. Reduced CPU some cores may be disabled. The system            Minor
     L-8004-   cache_ce            will continue to operate in the presence of this fault. System performance may be impacted due to disabled core(s).
     2E

40   SPINTE    fault.cpu.intel.    A processor has detected multiple memory controller correctable errors. Reduced CPU some cores may be disabled.           Minor
     L-8002-   mc_ce               The system will continue to operate in the presence of this fault. System performance may be impacted due to
     U2                            disabled processor.

41   SPINTE    fault.cpu.intel.    A processor has detected multiple Mid-Level Cache (MLC) correctable errors. Reduced CPU some cores may be                  Minor
     L-8002-   mlc_ce              disabled. The system will continue to operate in the presence of this fault. System performance may be impacted due
     XQ                            to disabled core(s).

42   SPINTE    fault.cpu.intel.    A processor has detected multiple memory controller address/command parity correctable errors. Reduced CPU                 Minor
     L-8002-   mc_addr_cmd_        some cores may be disabled. The system will continue to operate in the presence of this fault. System performance
     SE        parity_ce           may be impacted due to disabled processor.

43   SPINTE    fault.cpu.intel.    A processor detected internal correctable errors that exceed the SERD threshold. Reduced CPU some cores may be             Minor
     L-8009-   internal_ce         disabled. System will continue to operate
     48

44   SPINTE    defect.memory.      The custom refresh rate for temperature sensor has been disabled. Reduced Memory some dimms may be disabled.               Minor
     L-8001-   intel.mrc.          The system is able to boot however system performance may be impacted.
     WE        custom-refresh-
               rate-disabled

45   SPINTE    defect.memory.      The increased refresh rate for a temperature sensor has been disabled. Reduced Memory some dimms may be                    Minor
     L-8001-   intel.mrc.2x-       disabled. The system is able to boot however system performance may be impacted.
     VJ        refresh-rate-
               disabled

46   SPENV-    fault.chassis.      IOU GXR ERROR. ILOM is running Host won’t start. The system will continue to operate in the presence of this alert          Minor
     8001-77   config.iou.gxr-     but functionality may be reduced.
               error

47   SPINTE    defect.ilom.        BIOS has received an unexpected ereport that was received from the root port of a processor. No immediate impact to        Minor
     L-8007-   intel.bios-rppio-   the host. The system will continue to operate.
     SP        report-
               unexpected

48   SPINTE    defect.chassis.     The Platform Controller Hub (PCH) has been reset. Reprovision Required. The PCH has been reset but we don't                Minor
     L-8001-   intel.pch.reset-    know if the reset was successful.
     EX        result-
               unknown-
               nonserviceable

49   SPINTE    alert.memory.       The Memory Reference Code (MRC) has disabled Single Device Data Correction (SDDC). Reduced Memory some                     Minor
     L-8001-   intel.mrc.sddc-     dimms may be disabled. The system is able to boot. No memory DIMMs are disabled however advanced RAS
     73        disable             capabilities are impacted.

50   SPINTE    alert.memory.       The Memory Reference Code (MRC) has disabled Advanced Double Device Data Correction (ADDDC). Reduced                       Minor
     L-8000-   intel.mrc.          Memory some dimms may be disabled. The system is able to boot. No memory DIMMs are disabled however
     Y5        adddc-disable       advanced RAS capabilities are impacted.

51   SPINTE    alert.memory.       The Voltage Drain Drain (VDD) value set in the BIOS is not appropriate for the Data Center Persistent Memory Module         Minor
     L-8000-   intel.mrc.3dx.      (DCPMM) a.k.a. 3D Xpoint (3DX) DIMM's. Reduced Memory some dimms may be disabled. None. The hardware is
     XS        vdd-changed         not at fault and there is no bug with the firmware ( BIOS). The VDD value can be changed by the user in the BIOS
                                   configuration menu. The user should reload BIOS without preserving the configuration.

52   SPINTE    alert.io.pcie.      The number of PCIe link correctable errors (CEs) have exceeded threshold limit. No direct impact look for associated       Minor
     L-8007-   endpoint-link-      events. There is no impact to system operation.
     8S        ce-
               nonserviceable

53   SPINTE    alert.cpu.intel.    A burst of Ultrapath Interconnect (UPI) correctable link errors has occurred. This is a non-serviceable event used for      Minor
     L-8000-   ultrapath.          logging purposes to assist in other possible faults. No direct impact look for associated events. None. The system will
     9H        link_burst_ce_      continue to operate.
               nonserviceable

54   SPENV-    alert.chassis.      The power supplies are not providing redundant availability. Reduced power or cooling to the Server. None. Although        Minor
     8001-8G   power.              there is no impact to current operation system availability may be affected due to lack of redundant power supplies.
               redundancy-
               lost

55   SPINTE    alert.chassis.      The Platform Controller Hub (PCH) has momentarily failed to service a power-on request. No direct impact look for          Minor
     L-8000-   intel.pch.          associated events. The system can not be powered on when the PCH is in this condition.
     6R        power-on-
               request-denied-
               nonserviceable

56   SPINTE    alert.chassis.      A reset of the host has failed. No direct impact look for associated events. The system will be down temporarily while    Minor
     L-8000-   domain.intel.       the host boot is attempted.
     3E        pch.reset-
               failed-
               nonserviceable

57   SPENV-    alert.chassis.      IOU External Cable Missing. Configuration Issue after Repair. The system will continue to operate in the presence of        Minor
     8001-4M   config.iou.         this alert but functionality may be reduced.
               external-cable.
               missing
58   SPGXT     fault.io.pcie.     Indicates that a PCI link error has occurred on a sled of the G4-8c. Reduced Storage OR Network Performance.            Minor
     AIL-      link-degraded-     System will continue to operate however performance may be impacted.
     8000-Q8   speed

59   SPGX-     fault.gpu.mem.     Indicates that future GPU memory row mappings are not available. No immediate impact to the host. Any future GPU        Minor
     8000-LY   bank-row-          memory errors that are encountered may result in the system to go down immediately.
               remapping-
               unavailable

60   SPENV-    alert.chassis.     A fan module required to maintain redundancy is missing. Loss of redundant cooling. Configuration Issue after Repair.   Minor
     8000-70   config.fan.
               missing

61   SPENV-    alert.chassis.     A loss of AC input power to a power supply has been detected. Reduced power or cooling to the Server. Loss of           Minor
     8000-K6   power.ext-fail     redundant power.

62   SPENV-    alert.chassis.     FAN Low Speed. Configuration Issue after Repair. The system has reduced cooling capacity. Install high speed fans to    Minor
     8001-     config.fan.low-    properly cool the system.
     NU        speed

63   SPENV-    fault.chassis.     RTC Battery End of Life. No immediate impact to the host. ILOM and/or HOST time-of-day clock may not be retained        Minor
     8001-JK   battery.fail       or accurate when the RTC battery reaches its end of life.

64   ILOM-     defect.ilom.fdd.   ILOM fault manager has posted an ereport that has an invalid format or invalid contents. ILOM Impacted, No Impact to   Minor
     8000-M9   ereport-invalid    the Host. ILOM Impacted, No Impact to the Host. Upgrade to the latest version of ILOM.

65   SPGXT     alert.chassis.     GX Switch Thermtrip. Reduced CPU some cores may be disabled. Some PCI devices may become unavailable to                 Minor
     AIL-      gx.sw.thermtrip    applications. Do not replace the SLED
     8000-3K

66   SPGX-     alert.chassis.     GX GPU Thermtrip. Reduced CPU some cores may be disabled. The GPU is not available to applications. Do not              Minor
     8000-3D   gx.gpu.            replace the GPU
               thermtrip

67   ILOM-     defect.ilom.fs.    An ILOM file system has exceeded the file system capacity limit. ILOM Impacted No Impact to the Host. The service      Minor
     8000-79   logging-           processor may be unable to continue logging incoming events if the filesystem remains near full.
               misconfig
