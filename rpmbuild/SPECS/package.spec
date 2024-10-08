%define unmangled_name proton-vpn-killswitch-network-manager
%define version 0.6.1
%define release 1

Prefix: %{_prefix}

Name: python3-%{unmangled_name}
Version: %{version}
Release: %{release}%{?dist}
Summary: %{unmangled_name} library

Group: ProtonVPN
License: GPLv3
Vendor: Proton AG <opensource@proton.me>
URL: https://github.com/ProtonVPN/python-%{unmangled_name}
Source0: %{unmangled_name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot

BuildRequires: python3-setuptools
BuildRequires: NetworkManager
BuildRequires: python3-gobject
BuildRequires: python3-packaging
BuildRequires: python3-proton-vpn-api-core >= 0.35.2

Requires: NetworkManager
Requires: python3-gobject
Requires: python3-packaging
Requires: python3-proton-vpn-api-core >= 0.35.2

Conflicts: python3-proton-vpn-network-manager < 0.9.0

%{?python_disable_dependency_generator}

%description
Package %{unmangled_name} library.


%prep
%setup -n %{unmangled_name}-%{version} -n %{unmangled_name}-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES


%files -f INSTALLED_FILES
%{python3_sitelib}/proton/
%{python3_sitelib}/proton_vpn_killswitch_network_manager-%{version}*.egg-info/
%defattr(-,root,root)

%changelog
* Thu Sep 26 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.0
- Deprecate package.

* Mon Sep 23 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.0
- Drop logger package.

* Tue Aug 13 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.5.4
- Only log if kill switch backend is incompatible.

* Mon Aug 12 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.5.3
- Invert ipv6 detection logic.

* Fri Aug 09 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.5.2
- Improve error handling.

* Tue Aug 06 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.5.1
- Change kill switch method depending on IPv6 kernel setting.

* Thu Jul 11 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.5.0
- Add proton-vpn-api-core dependency

* Thu Jun 13 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.4.5
- Change kill switch connection IPv4 config from manual to auto.

* Tue Apr 30 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.4
- Fix random crashes when enabling/disabling the kill switch

* Wed Mar 06 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.3
- Fix crash on older distros when disabling connectivity checking

* Wed Feb 21 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.2
- Keep same old kill switch connection ids

* Tue Feb 20 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.1
- Fix switching between non-permanent and permanent KS

* Thu Feb 08 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.4.0
- Add permanent kill switch

* Wed Feb 07 2024 Josep Llaneras <josep.llaneras@proton.ch> 0.3.0
- Wait for target interface state when adding/removing NM connections

* Mon Sep 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.2.0
- Implement kill switch

* Tue Apr 04 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.1
- Rely on NMClient for connection handling

* Thu Mar 23 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.0
- Implement IPv6 leak protection

* Wed Jun 1 2022 Proton Technologies AG <opensource@proton.me> 0.0.1
- First RPM release
